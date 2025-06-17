import torch
import cv2
import asyncio
import websockets
import json
import base64
import numpy as np
from Metode import cari_warna_terdekat
from Metode import get_dominant_color_bg
from Metode import color_bgr
from Metode import encode_image_to_base64

# ==================== 1. INISIALISASI MODEL YOLO ====================

# Muat model YOLOv5s (versi kecil)
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)
model.conf = 0.5  # Set confidence threshold (hanya deteksi dengan confidence > 50%)

# ==================== 4. ANALISA GAMBAR DARI UPLOAD (TANPA WEBCAM) ====================
# Ini adalah versi server Python yang hanya menerima gambar diunggah.
# Jika Anda ingin tetap ada stream webcam DENGAN kemampuan upload,
# Anda harus kembali ke kode main.py sebelumnya dan menyesuaikannya.

async def handle_uploaded_image_analysis(websocket):
    print("[INFO] Server siap menerima gambar untuk analisa.")
    try:
        # Loop untuk terus menerima pesan dari klien
        async for message in websocket: 
            try:
                data_received = json.loads(message)
                
                if data_received.get('type') == 'upload_image':
                    print("[INFO] Menerima gambar yang diunggah untuk analisa.")
                    base64_image_data = data_received['image_base64']
                    
                    nparr = np.frombuffer(base64.b64decode(base64_image_data), np.uint8)
                    uploaded_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if uploaded_image is None:
                        print("[ERROR] Gagal mendekode gambar yang diunggah.")
                        await websocket.send(json.dumps({'type': 'error', 'message': 'Failed to decode image.'}))
                        continue

                    # --- BARU: Encode gambar asli TANPA modifikasi ---
                    original_image_base64 = encode_image_to_base64(uploaded_image)

                    # Buat salinan gambar untuk digambar deteksi
                    # Deteksi akan digambar di frame_with_detections, BUKAN di uploaded_image
                    frame_with_detections = uploaded_image.copy() 
                    
                    frame_rgb = cv2.cvtColor(frame_with_detections, cv2.COLOR_BGR2RGB)
                    results = model(frame_rgb)
                    detections = results.xyxy[0]
                    
                    detected_objects_data = []
                    
                    for i, (*box, conf, cls) in enumerate(detections):
                        x1, y1, x2, y2 = map(int, box)
                        label = model.names[int(cls)]
                        
                        # Potongan gambar diambil dari gambar asli yang diunggah (bukan dari frame_with_detections)
                        # Ini memastikan potongan gambar juga bersih dari deteksi lain yang digambar
                        cropped_image = uploaded_image[y1:y2, x1:x2] 
                        if cropped_image.size == 0:
                            continue
                        
                        dominant_color_bgr = get_dominant_color_bg(cropped_image)
                        dominant_color_rgb = (dominant_color_bgr[2], dominant_color_bgr[1], dominant_color_bgr[0])
                        warna_terdekat = cari_warna_terdekat(dominant_color_rgb)
                        
                        # Gambar bounding box dan label HANYA pada frame_with_detections
                        cv2.rectangle(frame_with_detections, (x1, y1), (x2, y2), color_bgr(dominant_color_rgb), 2)
                        cv2.putText(frame_with_detections, f"{label} - {warna_terdekat['color_name']}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr(dominant_color_rgb), 2)
                        
                        cropped_base64 = encode_image_to_base64(cropped_image)
                        
                        detected_objects_data.append({
                            'label': label,
                            'confidence': float(conf),
                            'bbox': [x1, y1, x2, y2],
                            'dominant_color_rgb': dominant_color_rgb,
                            'color_name': warna_terdekat['color_name'],
                            'color_code': warna_terdekat['color_code'],
                            'cropped_image_base64': cropped_base64
                        })
                    
                    response_data = {
                        'type': 'analysis_result',
                        'source': 'uploaded_image',
                        'original_image_base64': original_image_base64, # Mengirim gambar asli untuk mainFrameImage
                        'detections': detected_objects_data # Deteksi untuk frame-frame kecil
                    }
                    await websocket.send(json.dumps(response_data))
                    print("[INFO] Hasil analisa gambar yang diunggah dikirim.")

                else:
                    print(f"[WARN] Pesan dengan tipe tidak dikenal diterima: {data_received.get('type')}")
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Unknown message type. Only "upload_image" is supported.'}))

            except json.JSONDecodeError:
                print(f"[ERROR] Menerima pesan non-JSON atau JSON tidak valid: {message[:50]}...")
            except Exception as e:
                print(f"[ERROR] Terjadi kesalahan saat memproses pesan: {e}")

    except websockets.exceptions.ConnectionClosedOK:
        print("[INFO] Koneksi WebSocket ditutup normal.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[ERROR] Koneksi WebSocket ditutup dengan error: {e}")
    except Exception as e:
        print(f"[ERROR] Kesalahan tak terduga pada server: {e}")

async def main(): 
    server = await websockets.serve(handle_uploaded_image_analysis, "192.168.9.66", 1225)
    print("Server YOLO berjalan di ws://192.168.9.66:1225. Menunggu gambar yang diunggah...")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())