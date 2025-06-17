import torch
import cv2
import asyncio
import websockets
import json
from Metode import cari_warna_terdekat
from Metode import get_dominant_color
from Metode import color_bgr
from Metode import encode_image_to_base64


# ==================== 1. INISIALISASI MODEL YOLO ====================

# Muat model YOLOv5s (versi kecil)
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)
model.conf = 0.5  # Set confidence threshold (hanya deteksi dengan confidence > 50%)

# ==================== 4. REAL-TIME DETECTION DENGAN WEBCAM ====================

async def capture_image(websocket): 
    
    # Buka webcam (device 0 biasanya adalah webcam utama)
    cap = cv2.VideoCapture(0)

    print("[INFO] Deteksi real-time dimulai. Tekan 'q' untuk keluar.")  

    while True:
        # Baca frame dari webcam
        ret, frame = cap.read()
        if not ret:
            break
        
        # Konversi BGR ke RGB (karena YOLO mengharapkan input RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Lakukan deteksi objek dengan YOLO
        results = model(frame_rgb)
        detections = results.xyxy[0]  # Format: [x1, y1, x2, y2, confidence, class]

        # Tambahan jun 10 01.50
        # List untuk menyimpan data deteksi (termasuk potongan gambar)
        detected_objects_data = []
        
        # Proses setiap deteksi
        for i, (*box, conf, cls) in enumerate(detections):
            x1, y1, x2, y2 = map(int, box)
            label = model.names[int(cls)]  # Dapatkan nama kelas dari ID kelas
            
            # Potong ROI (Region of Interest) berdasarkan bounding box
            cropped = frame[y1:y2, x1:x2]
            
            # Skip jika ROI kosong
            if cropped.size == 0:
                continue
            
            # Dapatkan warna dominan dari ROI
            dominant_color_bgr = get_dominant_color(cropped)
            
            # Ubah ke rgb
            dominant_color_rgb = (dominant_color_bgr[2], dominant_color_bgr[1], dominant_color_bgr[0])

            # Cari warna terdekat dari dataset
            warna_terdekat = cari_warna_terdekat(dominant_color_rgb)
            
            # Format teks label
            label_text = f"{label} - {warna_terdekat['color_name']}"
            
            # Gambar bounding box dengan warna dominan
            cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr(dominant_color_rgb), 2)
            
            # Tampilkan label di atas bounding box
            cv2.putText(frame, label_text, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr(dominant_color_rgb), 2)
            
            # Cetak informasi ke konsol
            # print(f"\nDeteksi ke-{i+1}:")
            # print(f"Objek: {label}")
            # print(f"Posisi: ({x1}, {y1}) ke ({x2}, {y2})")
            # print(f"Warna dominan: RGB {dominant_color_rgb}")
            # print(f"Warna terdekat: {warna_terdekat['color_name']}")
            # print(f"Kode warna: {warna_terdekat['color_code']}")

            #Tambahan jun 10 01.49
            # Encode potongan gambar ke base64
            cropped_base64 = encode_image_to_base64(cropped)
            
            # Tambahkan data deteksi (termasuk potongan gambar) ke list
            detected_objects_data.append({
                'label': label,
                'confidence': float(conf),
                'bbox': [x1, y1, x2, y2],
                'dominant_color_rgb': dominant_color_rgb,
                'color_name': warna_terdekat['color_name'],
                'color_code': warna_terdekat['color_code'],
                'cropped_image_base64': cropped_base64
            })

        # ubah frme buffer ke base64 string 
        frame_kirim = encode_image_to_base64(frame)

        # Buat objek JSON yang berisi semua data
        data_to_send = {
            'full_frame_base64': frame_kirim,
            'detections': detected_objects_data
        }

        # Konversi dictionary ke string JSON
        json_data_str = json.dumps(data_to_send, indent=2)
        
        # Kirim data melalui WebSocket
        await websocket.send(json_data_str)
        await asyncio.sleep(0.01)

         # Cetak JSON ke konsol server (UNTUK DEBUGGING)
        # print("--- JSON DATA SENT ---")
        # print(json_data_str)
        # print("----------------------")
    
    # ==================== 5. CLEANUP ====================
    # Bebaskan resources
    cap.release()

async def main(): 
    
    server = await websockets.serve(capture_image, "192.168.9.66", 1234)
    print("Server running on http://192.168.9.66:1234")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())