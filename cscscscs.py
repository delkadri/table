import serial
import time
import math
from svgpathtools import svg2paths2
import xml.etree.ElementTree as ET

# === CONFIGURATION ===
SVG_FILE = "coeur.svg"
STEP_SIZE = 2           # distance entre points (mm)
MAX_SIZE = 200          # surface physique max (mm)
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

# === CALCUL AUTO DU SCALE ===
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

# === TRAITEMENT DE CHAQUE PATH ===
for path in paths:
    first_point = True  # début du path

    for segment in path:
        length = segment.length(error=1e-3)
        steps = max(1, int(length * SCALE / STEP_SIZE))

        for i in range(steps + 1):
            point = segment.point(i / steps)
            x = point.real * SCALE
            y = point.imag * SCALE

            if first_point:
                # Déplacer sans dessiner
                if (current_x != x or current_y != y):
                    send_command("PEN_UP")
                    send_command(f"MOVE X={x:.2f} Y={y:.2f}")
                    current_x, current_y = x, y
                send_command("PEN_DOWN")
                first_point = False

            # Avancer vers le point suivant
            send_command(f"MOVE X={x:.2f} Y={y:.2f}")
            current_x, current_y = x, y

    # À la fin du path, lever le stylo
    send_command("PEN_UP")

# === FIN DU DESSIN ===
send_command("PEN_UP")
send_command("END")
ser.close()
print(" Dessin terminé. Port série fermé.")
