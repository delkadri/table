import serial
import time
import math
from svgpathtools import svg2paths2
import xml.etree.ElementTree as ET

# === CONFIGURATION ===
SVG_FILE = "ton_image.svg"     # Remplace par ton fichier
STEP_SIZE = 2                  # mm
MAX_SIZE = 200                 # mm (côté max de ta surface)
SERIAL_PORT = "/dev/ttyUSB0"   # À adapter
BAUD_RATE = 115200

# === CONNEXION SÉRIE ===
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

def is_far_enough(x1, y1, x2, y2, threshold=0.01):
    return math.hypot(x2 - x1, y2 - y1) > threshold

# === NOUVELLE MÉTHODE : BOUNDS RÉELS ===
def calculate_real_bounds(paths):
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for path in paths:
        for seg in path:
            for t in [0.0, 0.25, 0.5, 0.75, 1.0]:  # 5 points pour chaque segment
                pt = seg.point(t)
                x, y = pt.real, pt.imag
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    width = max_x - min_x
    height = max_y - min_y
    return width, height

# === LECTURE DES PATHS ET CALCUL DU SCALE ===
paths, attributes, svg_attributes = svg2paths2(SVG_FILE)
real_width, real_height = calculate_real_bounds(paths)
SCALE = min(MAX_SIZE / real_width, MAX_SIZE / real_height)
print(f"Dimensions réelles du dessin : {real_width:.1f} x {real_height:.1f} px → SCALE: {SCALE:.4f}")

# === TRACÉ ===
current_x, current_y = 0, 0

for path in paths:
    for segment in path:
        length = segment.length(error=1e-3)
        steps = max(1, int(length * SCALE / STEP_SIZE))

        for i in range(steps + 1):
            point = segment.point(i / steps)
            x = point.real * SCALE
            y = point.imag * SCALE

            if i == 0:
                if is_far_enough(current_x, current_y, x, y):
                    send_command("PEN_UP")
                    send_command(f"MOVE X={x:.2f} Y={y:.2f}")
                    current_x, current_y = x, y
                send_command("PEN_DOWN")

            send_command(f"MOVE X={x:.2f} Y={y:.2f}")
            current_x, current_y = x, y

    send_command("PEN_UP")

# === FIN ===
send_command("PEN_UP")
send_command("END")
ser.close()
print("Dessin terminé. Port série fermé.")
