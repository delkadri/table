import serial
import time
import math
from svgpathtools import svg2paths2

# === CONFIGURATION ===
SVG_FILE = "triangle-svgrepo-com.svg"
STEP_SIZE = 5       # mm
SCALE = 5           # Ex: 1px = 5mm
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
TOLERANCE_CM = 0.5  # tolérance max entre cible et position réelle

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

def attendre_et_verifier_position_attendue(x_cible, y_cible, tolerance=0.5, timeout=2):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open("position_reelle.txt", "r") as f:
                contenu = f.read().strip()
                x_reel, y_reel = map(float, contenu.split(","))
                dx = abs(x_reel - x_cible)
                dy = abs(y_reel - y_cible)
                if dx <= tolerance and dy <= tolerance:
                    return True
        except:
            pass
        time.sleep(0.1)
    return False

# === TRAITEMENT DU SVG ===
paths, attributes, svg_attributes = svg2paths2(SVG_FILE)
current_x, current_y = 0, 0

for path in paths:
    for segment in path:
        start = segment.start
        end = segment.end

        x_start, y_start = start.real * SCALE, start.imag * SCALE
        x_end, y_end = end.real * SCALE, end.imag * SCALE

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

            # Vérification de la position réelle
            ok = attendre_et_verifier_position_attendue(new_x, new_y, tolerance=TOLERANCE_CM)
            if not ok:
                print("Erreur : position incorrecte. Retour au point précédent.")
                send_command("PEN_UP")
                send_command(f"MOVE X={x_start:.2f} Y={y_start:.2f}")
                break  # ou continue si tu veux sauter le point
        send_command(f"MOVE X={x_end:.2f} Y={y_end:.2f}")
        current_x, current_y = x_end, y_end

    send_command("PEN_UP")

send_command("PEN_UP")
send_command("END")
ser.close()
print("Dessin terminé. Port série fermé.")
