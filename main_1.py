#SANS TRAITEMENT DE COURBE AVEC SCALE
import serial
import time
import math
from svgpathtools import svg2paths2
from xml.etree import ElementTree as ET

# === CONFIGURATION ===
SVG_FILE = "coeur.svg"
STEP_SIZE = 2       # mm
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
MAX_SIZE = 300  

print("Connexion à l'ESP32...")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)
print("Connexion établie !")

def send_command(cmd):
    ser.write((cmd + "\n").encode())
    print("→", cmd)
    while True:
        response = ser.readline().decode().strip()
        if response == "OK":
            break
        elif response:
            print("← ESP32:", response)


def calculate_scale(svg_file, max_size=MAX_SIZE):
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Vérifier la présence du viewBox
    viewBox = root.attrib.get('viewBox')
    if viewBox:
        # Si le viewBox est présent, il contient les informations sur la taille réelle de l'image
        viewBox_values = viewBox.split()
        width = float(viewBox_values[2])
        height = float(viewBox_values[3])
    else:
        # Si pas de viewBox, essayer d'extraire les dimensions width et height
        width = float(root.attrib.get('width', '0').replace('px', '').strip())
        height = float(root.attrib.get('height', '0').replace('px', '').strip())

    # Calculer le facteur de mise à l'échelle basé sur les dimensions maximales
    scale_x = max_size / width
    scale_y = max_size / height

    # Le facteur de mise à l'échelle doit être le plus petit pour éviter que l'image dépasse
    scale = min(scale_x, scale_y)

    print(f"Dimensions de l'image SVG: {width}x{height} pixels")
    print(f"Facteur de mise à l'échelle calculé: {scale:.4f}")

    return scale

# Calculer automatiquement le scale
SCALE = calculate_scale(SVG_FILE)

# Charger le SVG
paths, attributes, svg_attributes = svg2paths2(SVG_FILE)
current_x, current_y = 0, 0

for path in paths:
    for segment in path:
        start = segment.start
        end = segment.end

        x_start, y_start = start.real * SCALE, start.imag * SCALE
        x_end, y_end = end.real * SCALE, end.imag * SCALE

        # Aller au point de départ si nécessaire
        if (current_x != x_start or current_y != y_start):
            send_command("PEN_UP")
            send_command(f"MOVE X={x_start:.2f} Y={y_start:.2f}")
            current_x, current_y = x_start, y_start

        send_command("PEN_DOWN")

        dx = x_end - x_start
        dy = y_end - y_start
        distance = math.hypot(dx, dy)
        steps = max(1, int(distance / STEP_SIZE))

        for i in range(1, steps + 1):
            new_x = x_start + (dx / steps) * i
            new_y = y_start + (dy / steps) * i
            send_command(f"MOVE X={new_x:.2f} Y={new_y:.2f}")

        # Assure d’arriver à la fin exacte
        send_command(f"MOVE X={x_end:.2f} Y={y_end:.2f}")
        current_x, current_y = x_end, y_end

    send_command("PEN_UP")

send_command("PEN_UP")
send_command("END")
ser.close()
print("Dessin terminé. Port série fermé.")