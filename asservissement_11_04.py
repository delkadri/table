import cv2
import numpy as np
from picamera2 import Picamera2

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

SCALE = 5  # pixels par cm
origin_red = None  # Origine du repère (à définir dynamiquement)

print("Détection en cours... Appuyez sur 'q' pour quitter, 'r' pour réinitialiser l'origine.")

try:
    while True:
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Détection du point rouge
        lower_red = np.array([0, 0, 170])
        upper_red = np.array([64, 64, 255])
        mask_red = cv2.inRange(frame_bgr, lower_red, upper_red)
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        point_rouge = None
        if contours_red:
            largest_red = max(contours_red, key=cv2.contourArea)
            M = cv2.moments(largest_red)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                point_rouge = (cX, cY)
                cv2.circle(frame_bgr, point_rouge, 10, (0, 255, 0), -1)

                if origin_red is None:
                    origin_red = (cX, cY)
                    print(f"[Origine] Fixée à : {origin_red}")

        # Détection des points bleus (optionnel)
        lower_blue = np.array([150, 0, 0])
        upper_blue = np.array([255, 100, 100])
        mask_blue = cv2.inRange(frame_bgr, lower_blue, upper_blue)
        contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours_blue:
            area = cv2.contourArea(contour)
            if area > 100:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    bx = int(M["m10"] / M["m00"])
                    by = int(M["m01"] / M["m00"])
                    cv2.circle(frame_bgr, (bx, by), 8, (255, 0, 0), -1)

        # Position relative
        if origin_red and point_rouge:
            dx_cm = (cX - origin_red[0]) / SCALE
            dy_cm = (origin_red[1] - cY) / SCALE

            with open("position_relative.txt", "w") as f:
                f.write(f"{dx_cm:.2f},{dy_cm:.2f}")

            print(f"[Position] X = {dx_cm:.2f} cm, Y = {dy_cm:.2f} cm")
            cv2.putText(frame_bgr, f"X: {dx_cm:.2f} cm, Y: {dy_cm:.2f} cm",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 2)

        cv2.imshow("Live Stream", frame_bgr)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('r'):
            origin_red = None
            print("[Reset] Origine réinitialisée. Placez le point rouge pour fixer une nouvelle origine.")

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    print("Capture et détection terminées.")
