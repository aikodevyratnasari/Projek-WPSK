import cv2

cap = cv2.VideoCapture(2)

while True :
    ret, frame = cap.read()

    if not ret:
        break

    cv2.imshow("Deteksi Objek dan Warna", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
