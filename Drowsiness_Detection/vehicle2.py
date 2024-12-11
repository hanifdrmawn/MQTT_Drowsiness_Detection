from scipy.spatial import distance
from imutils import face_utils
import pygame  # type: ignore
import imutils
import dlib
import cv2
import paho.mqtt.client as mqtt  # type: ignore

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Constants
thresh = 0.25
frame_check = 50
Plat_Nomor = "N649PQL"
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = f"sensor/drowsiness/{Plat_Nomor}"

# Dlib setup
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]

# MQTT setup
client = mqtt.Client(client_id="DrowsinessDetector")
flag = 0

# Callback function for receiving messages
def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    if "Tidak Diizinkan Mengemudi" in payload:
        print("Kendaraan ini tidak boleh beroperasi karena pengendara mengantuk.")
        # Stop MQTT loop and cleanup resources
        client.loop_stop()
        cap.release()  # Ensure the video capture is released
        cv2.destroyAllWindows()
        os._exit(0)  # Immediate termination
        # exit()

client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT)
client.subscribe(MQTT_TOPIC)

# Initialize video capture
cap = cv2.VideoCapture(0)
client.loop_start()

while True:
    ret, frame = cap.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    subjects = detect(gray, 0)

    for subject in subjects:
        shape = predict(gray, subject)
        shape = face_utils.shape_to_np(shape)
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0

        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        if ear < thresh:
            flag += 1
            print(flag)
            if flag >= frame_check:
                cv2.putText(frame, "****************ALERT!****************", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, "****************ALERT!****************", (10, 325),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                client.publish(MQTT_TOPIC, "Drowsiness detected!")
                print("Drowsiness alert sent to MQTT broker!")

                pygame.mixer.init()
                pygame.mixer.music.load("sirene.wav")
                pygame.mixer.music.play()
                flag = 0
        else:
            flag = 0

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Cleanup
cv2.destroyAllWindows()
cap.release()
client.loop_stop()
