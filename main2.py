import serial
import time
import math
from svgpathtools import svg2paths2, CubicBezier

# === CONFIGURATION ===
SVG_FILE = "image_svg.svg"
STEP_SIZE = 2       # mm
SCALE = 5           # Ex: 1px = 0.1mm (à ajuster)
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

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

# Fonction pour diviser une courbe de Bézier cubique en segments linéaires
def cubic_bezier_to_lines(p0, p1, p2, p3, step_size):
    lines = []
    for t in range(1, int(1 / step_size) + 1):
        t /= (1 / step_size)
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        lines.append((x, y))
    return lines

# Charger le SVG
paths, attributes, svg_attributes = svg2paths2(SVG_FILE)
current_x, current_y = 0, 0

for path in paths:
    for segment in path:
        if isinstance(segment, CubicBezier):
            # Pour une courbe de Bézier cubique
            start = segment.start
            end = segment.end
            p0 = segment.control1
            p1 = segment.control2

            x_start, y_start = start.real * SCALE, start.imag * SCALE
            x_end, y_end = end.real * SCALE, end.imag * SCALE

            # Convertir la courbe de Bézier en segments linéaires
            line_segments = cubic_bezier_to_lines((x_start, y_start), (p0.real * SCALE, p0.imag * SCALE), 
                                                  (p1.real * SCALE, p1.imag * SCALE), 
                                                  (x_end, y_end), STEP_SIZE)

            # Aller au point de départ si nécessaire
            if (current_x != x_start or current_y != y_start):
                send_command("PEN_UP")
                send_command(f"MOVE X={x_start:.2f} Y={y_start:.2f}")
                current_x, current_y = x_start, y_start

            send_command("PEN_DOWN")

            # Dessiner la courbe approximée par des segments
            for (new_x, new_y) in line_segments:
                send_command(f"MOVE X={new_x:.2f} Y={new_y:.2f}")
                current_x, current_y = new_x, new_y

        else:
            # Pour les segments linéaires
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

            # Déplacer le stylo en segments linéaires
            for i in range(1, steps + 1):
                new_x = x_start + (dx / steps) * i
                new_y = y_start + (dy / steps) * i
                send_command(f"MOVE X={new_x:.2f} Y={new_y:.2f}")
                current_x, current_y = new_x, new_y

    send_command("PEN_UP")

send_command("END")
ser.close()
print("Dessin terminé. Port série fermé.")
