import serial
import time
import math
from svgpathtools import svg2paths2
import xml.etree.ElementTree as ET

# === CONFIGURATION ===
SVG_FILE = "coeur.svg"
STEP_SIZE = 2           # distance entre points (mm)
MAX_SIZE = 200          # surface physique (mm)
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# === OUVERTURE DU PORT SÉRIE ===
print("Connexion à l'ESP32...")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)
print("Connexion établie !")

# === ENVOI DE COMMANDE À L'ESP32 ===
def send_command(cmd):
    ser.write((cmd + "\n").encode())
    print("→", cmd)
    while True:
        response = ser.readline().decode().strip()
        if response == "OK":
            break
        elif response:
            print("← ESP32:", response)

# === CALCUL SCALE À PARTIR DE LA TAILLE DU SVG ===
def calculate_scale(svg_file, max_size=MAX_SIZE):
    tree = ET.parse(svg_file)
    root = tree.getroot()
    viewBox = root.attrib.get('viewBox')
    if viewBox:
        vb = list(map(float, viewBox.split()))
        width = vb[2]
        height = vb[3]
    else:
        width = float(root.attrib.get('width', '0').replace('px', '').strip())
        height = float(root.attrib.get('height', '0').replace('px', '').strip())

    scale = min(max_size / width, max_size / height)
    print(f"SVG dimensions: {width:.1f} x {height:.1f} px → SCALE: {scale:.3f}")
    return scale

SCALE = calculate_scale(SVG_FILE)

# === CHARGEMENT DU SVG ===
paths, attributes, svg_attributes = svg2paths2(SVG_FILE)
current_x, current_y = 0, 0

# === TRAITEMENT DE CHAQUE SEGMENT ===
for path in paths:
    for segment in path:
        length = segment.length(error=1e-3)  # longueur de la courbe
        steps = max(1, int(length * SCALE / STEP_SIZE))  # nombre de segments à générer

        # Interpolation en points
        for i in range(steps + 1):
            point = segment.point(i / steps)
            x = point.real * SCALE
            y = point.imag * SCALE

            if i == 0:
                # Début d’un nouveau segment : lever le stylo si nécessaire
                if (current_x != x or current_y != y):
                    send_command("PEN_UP")
                    send_command(f"MOVE X={x:.2f} Y={y:.2f}")
                    current_x, current_y = x, y
                send_command("PEN_DOWN")

            # Déplacer le stylo
            send_command(f"MOVE X={x:.2f} Y={y:.2f}")
            current_x, current_y = x, y

    # Lever le stylo entre chaque path
    send_command("PEN_UP")

# === FIN ===
send_command("PEN_UP")
send_command("END")
ser.close()
print(" Dessin terminé. Port série fermé.")
