import cv2
import numpy as np

from picamera2 import Picamera2



# Initialisation de la camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

pixels_per_cm = 10  # echelle fictive

print("Detection en cours... Appuyez sur 'q' pour quitter.")


try:
    while True:
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        ### Detection du point rouge en BGR ###
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

        ### Detection des points bleus en BGR ###
        lower_blue = np.array([150, 0, 0])
        upper_blue = np.array([255, 100, 100])
        mask_blue = cv2.inRange(frame_bgr, lower_blue, upper_blue)
        contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        blue_points = []
        for contour in contours_blue:
            area = cv2.contourArea(contour)
            if area > 100:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    bx = int(M["m10"] / M["m00"])
                    by = int(M["m01"] / M["m00"])
                    blue_points.append((bx, by))
                    cv2.circle(frame_bgr, (bx, by), 8, (255, 0, 0), -1)

        ### Definition du repere (0,0) et calcul des coordonnees relatives ###
        if len(blue_points) >= 2 and point_rouge:
            x_coords = [p[0] for p in blue_points]
            y_coords = [p[1] for p in blue_points]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)

            # Dessiner le cadre
            cv2.rectangle(frame_bgr, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)

            # On choisit le coin **bas gauche** comme origine
            origin_x = min_x
            origin_y = max_y  # car y augmente vers le bas en image

            # Calcul position locale en cm
            local_x_cm = (cX - origin_x) / pixels_per_cm
            local_y_cm = (origin_y - cY) / pixels_per_cm  # inversion car image vers le bas

            # Verification du cadre
            if origin_x <= cX <= max_x and min_y <= cY <= origin_y:
                print(f"Position du point rouge (repere local) : X = {local_x_cm:.2f} cm, Y = {local_y_cm:.2f} cm")
            else:
                cv2.putText(frame_bgr, "?? Hors cadre", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Affichage
        cv2.imshow("Live Stream", frame_bgr)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    print("Capture et detection terminees.")
