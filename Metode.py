import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from rembg import remove
from PIL import Image
import base64

# ==================== 1. LOAD DATASET WARNA DAN TRAIN KNN ====================

# Load dataset warna
dataset = pd.read_csv("colors.csv")

# Siapkan data training untuk KNN
X = dataset[['r', 'g', 'b']].values
y = dataset['color_string'].values

# Train model KNN
knn = KNeighborsClassifier(n_neighbors=1)
knn.fit(X, y)

# ==================== 2. DEFINISI FUNGSI PENDUKUNG ====================

def cari_warna_terdekat(rgb):
    """Mencari warna terdekat dari dataset berdasarkan nilai RGB"""
    r, g, b = rgb
    input_rgb = np.array([[r, g, b]])
    distances, indices = knn.kneighbors(input_rgb)
    
    warna_terdekat = dataset.iloc[indices[0][0]]
    return {
        'color_name': warna_terdekat['color_string'],
        'color_code': warna_terdekat['code'],
        'color_rgb': (warna_terdekat['r'], warna_terdekat['g'], warna_terdekat['b']),
        'distance': distances[0][0]
    }

def get_dominant_color(image, k=3):
    """Mendapatkan warna dominan dari gambar menggunakan K-Means clustering"""
    # # Hapus bg image
    # bgremove = remove(image)

    # # Ubah format rgba ke rgb
    # rgb_image_1 = cv2.cvtColor(bgremove, cv2.COLOR_RGBA2RGB)
    
    # Resize gambar untuk mempercepat proses
    image = cv2.resize(image, (50, 50))
    
    # Ubah bentuk gambar menjadi array 2D (setiap baris mewakili satu piksel)
    pixels = image.reshape((-1, 3))

    # Filter warna gambar tanpa bg 
    # mask = ~((pixels == [0, 0, 0]).all(axis=1) | (pixels == [255, 255, 255]).all(axis=1))
    # filtered_pixels = pixels[mask]
    
    # Lakukan clustering warna dengan K-Means
    kmeans = KMeans(n_clusters=k, n_init='auto')
    kmeans.fit(pixels)
    
    # Hitung jumlah piksel di setiap cluster
    counts = Counter(kmeans.labels_)
    
    # Ambil warna dari cluster dengan anggota terbanyak
    dominant = kmeans.cluster_centers_[counts.most_common(1)[0][0]]
    
    # Konversi ke integer (nilai RGB harus integer 0-255)
    return tuple(map(int, dominant))

def get_dominant_color_bg(image, k=3):
    """Mendapatkan warna dominan dari gambar menggunakan K-Means clustering"""
    # Hapus bg image
    bgremove = remove(image)

    # Ubah format rgba ke rgb
    rgb_image_1 = cv2.cvtColor(bgremove, cv2.COLOR_RGBA2RGB)
    
    # Resize gambar untuk mempercepat proses
    image = cv2.resize(rgb_image_1, (50, 50))
    
    # Ubah bentuk gambar menjadi array 2D (setiap baris mewakili satu piksel)
    pixels = image.reshape((-1, 3))

    # Filter warna gambar tanpa bg 
    mask = ~((pixels == [0, 0, 0]).all(axis=1) | (pixels == [255, 255, 255]).all(axis=1))
    filtered_pixels = pixels[mask]
    
    # Lakukan clustering warna dengan K-Means
    kmeans = KMeans(n_clusters=k, n_init='auto')
    kmeans.fit(filtered_pixels)
    
    # Hitung jumlah piksel di setiap cluster
    counts = Counter(kmeans.labels_)
    
    # Ambil warna dari cluster dengan anggota terbanyak
    dominant = kmeans.cluster_centers_[counts.most_common(1)[0][0]]
    
    # Konversi ke integer (nilai RGB harus integer 0-255)
    return tuple(map(int, dominant))

def color_bgr(rgb_tuple):
    """Konversi dari RGB ke BGR (format warna OpenCV)"""
    return tuple(reversed(rgb_tuple))

# Fungsi untuk mengkodekan gambar ke base64
def encode_image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 70]) # Kualitas 70%
    return base64.b64encode(buffer).decode('utf-8')