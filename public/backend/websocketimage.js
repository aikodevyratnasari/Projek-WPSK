// websocket.js

// Mendapatkan referensi elemen HTML
const mainFrameImage = document.getElementById("mainFrameImage");
const detectionBoxes = [1, 2, 3, 4, 5, 6].map((i) => ({
  container: document.getElementById(`detection-box-${i}`),
  label: document.getElementById(`label-${i}`),
  image: document.getElementById(`image-${i}`),
  colorName: document.getElementById(`color-name-${i}`),
  colorCode: document.getElementById(`color-code-${i}`),
  colorBox: document.getElementById(`color_box_${i}`),
}));

// Mendapatkan elemen input file dan tombol dari Grid 16
const imageUpload = document.getElementById("imageUpload");
const sendImageButton = document.getElementById("sendImageButton");

// Mendapatkan referensi ke elemen status dan error (pastikan ini ada di HTML Anda jika ingin menggunakannya)
// const statusMessage = document.getElementById("statusMessage"); // Uncomment jika ada di HTML
// const errorMessage = document.getElementById("errorMessage");   // Uncomment jika ada di HTML

// Fungsi untuk mereset tampilan kotak deteksi ke placeholder
function resetDetectionBoxes() {
  detectionBoxes.forEach((box) => {
    box.label.textContent = "Objek: Belum ada object terdeteksi";
    box.image.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="; // Gambar placeholder transparan
    box.colorName.textContent = "Warna: Tidak ada warna terdeteksi";
    box.colorCode.textContent = "Kode: Tidak ada kode warna terdeteksi";
    box.colorCode.style.color = "#1F2937"; // Pastikan teks hitam
    if (box.colorBox) {
      box.colorBox.style.backgroundColor = "#E5E7EB"; // Warna default abu-abu muda
    }
  });
}

// Inisialisasi tampilan awal
resetDetectionBoxes();
mainFrameImage.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="; // Placeholder untuk gambar utama

// Inisialisasi koneksi WebSocket
// Pastikan server Python Anda adalah yang menjalankan YOLO (ws://localhost:1234)
const socket = new WebSocket("ws://localhost:1225");

socket.onopen = () => {
  console.log("Connected to YOLO WebSocket server (localhost:1234)");
  // Jika statusMessage ada di HTML:
  // if (statusMessage) statusMessage.textContent = "Status: Terhubung ke server. Unggah gambar untuk analisa.";
  // if (errorMessage) errorMessage.textContent = ""; 
  alert("Terhubung ke server deteksi warna. Unggah gambar untuk analisa."); // Contoh feedback
};

socket.onmessage = function (event) {
  try {
    const data = JSON.parse(event.data); // Data adalah JSON

    // Memastikan ini adalah hasil analisa dari gambar yang diunggah
    if (data.type === "analysis_result" && data.source === "uploaded_image") {
      console.log("Hasil analisa gambar yang diunggah diterima dari YOLO.");
      // if (statusMessage) statusMessage.textContent = "Status: Analisa selesai. Hasil ditampilkan.";
      // if (errorMessage) errorMessage.textContent = ""; 

      // --- BARIS KUNCI: Menampilkan gambar asli yang diunggah di mainFrameImage ---
      if (data.original_image_base64) {
          mainFrameImage.src = `data:image/jpeg;base64,${data.original_image_base64}`;
      } else {
          // Fallback jika original_image_base64 tidak ada (misalnya dari server lama atau stream webcam)
          mainFrameImage.src = `data:image/jpeg;base64,${data.full_frame_base64}`;
      }
      
      // --- BARIS KUNCI: Memperbarui kotak deteksi kecil dengan hasil deteksi objek ---
      updateDetectionBoxes(data.detections);

    } else if (data.type === "webcam_stream") {
      // Jika server YOLO Anda masih mengirim stream webcam secara default, Anda bisa menangani di sini.
      // Saat ini, log ini hanya untuk informasi dan mengabaikannya karena fokus pada upload gambar.
      console.log("Menerima stream webcam (diabaikan karena fokus pada upload gambar).");
      // Jika ingin menampilkannya:
      // if (statusMessage) statusMessage.textContent = "Status: Live stream webcam...";
      // mainFrameImage.src = `data:image/jpeg;base64,${data.full_frame_base64}`;
      // updateDetectionBoxes(data.detections);
    } 
    else if (data.type === "error") {
      console.error("Server Error (YOLO):", data.message);
      // if (statusMessage) statusMessage.textContent = "Status: Terjadi Error!";
      // if (errorMessage) errorMessage.textContent = "Error dari server: " + data.message;
      alert("Error dari server: " + data.message); // Tetap pakai alert untuk error kritis
      mainFrameImage.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="; // Reset gambar utama
      resetDetectionBoxes(); // Reset kotak deteksi
    } else {
      console.log("Menerima tipe pesan tidak dikenal dari YOLO:", data.type, data);
      // if (statusMessage) statusMessage.textContent = "Status: Menerima pesan tak dikenal.";
    }
  } catch (e) {
    console.error("Failed to parse JSON or update elements:", e, event.data);
    // if (statusMessage) statusMessage.textContent = "Status: Gagal memproses data.";
    // if (errorMessage) errorMessage.textContent = "Error: Gagal memproses data dari server.";
    alert("Gagal memproses data dari server. Lihat konsol."); // Tetap pakai alert untuk error parsing
  }
};

socket.onclose = () => {
  console.log("Disconnected from YOLO WebSocket server");
  // if (statusMessage) statusMessage.textContent = "Status: Terputus dari server.";
  // if (errorMessage) errorMessage.textContent = "Koneksi terputus. Harap muat ulang halaman.";
  alert("Terputus dari server. Harap muat ulang halaman jika ingin terhubung kembali."); // Tetap pakai alert
};

socket.onerror = (error) => {
  console.error("WebSocket error (YOLO):", error);
  // if (statusMessage) statusMessage.textContent = "Status: Kesalahan koneksi!";
  // if (errorMessage) errorMessage.textContent = "Error WebSocket: " + error.message;
  alert("Terjadi kesalahan WebSocket. Lihat konsol untuk detail."); // Tetap pakai alert
};

// Listener untuk tombol kirim gambar
sendImageButton.addEventListener("click", () => {
  const file = imageUpload.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64Image = e.target.result.split(",")[1]; // Menghapus bagian "data:image/..."

      const uploadData = {
        type: "upload_image", // Tipe pesan harus sesuai dengan server YOLO
        image_base64: base64Image, // Kunci data gambar harus sesuai
      };

      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(uploadData));
        console.log("Gambar dikirim untuk analisa.");
        // if (statusMessage) statusMessage.textContent = "Status: Gambar dikirim. Menunggu analisa...";
        // if (errorMessage) errorMessage.textContent = "";

        // Atur tampilan menjadi loading/menganalisa
        mainFrameImage.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="; // Kosongkan/loading
        updateDetectionBoxes([]); // Kosongkan kotak deteksi saat mengirim
      } else {
        console.warn("WebSocket tidak terbuka. Tidak bisa mengirim gambar.");
        // if (statusMessage) statusMessage.textContent = "Status: Gagal mengirim.";
        // if (errorMessage) errorMessage.textContent = "Koneksi ke server tidak terbuka. Pastikan server berjalan.";
        alert("Koneksi ke server tidak terbuka. Pastikan server berjalan."); // Tetap pakai alert
      }
    };
    reader.readAsDataURL(file); // Membaca file sebagai Data URL
  } else {
    console.log("Pilih gambar terlebih dahulu!");
    // if (statusMessage) statusMessage.textContent = "Status: Pilih gambar terlebih dahulu.";
    // if (errorMessage) errorMessage.textContent = "Error: Anda harus memilih gambar.";
    alert("Pilih gambar terlebih dahulu!"); // Tetap pakai alert
  }
});

// Fungsi helper untuk update detection boxes (pastikan ini ada di sini atau diimpor)
function updateDetectionBoxes(detectionsData) {
  detectionBoxes.forEach((box, index) => {
    if (detectionsData && detectionsData[index]) {
      const detection = detectionsData[index];
      box.label.textContent = `Objek: ${detection.label}`;
      box.image.src = `data:image/jpeg;base64,${detection.cropped_image_base64}`;
      box.colorName.textContent = `Warna: ${detection.color_name}`;
      box.colorCode.textContent = `Kode: ${detection.color_code}`;
      box.colorCode.style.color = "#1F2937"; // Teks kode warna tetap hitam
      if (box.colorBox) {
        box.colorBox.style.backgroundColor = detection.color_code;
      }
    } else {
      // Reset atau tampilkan placeholder jika tidak ada deteksi
      box.label.textContent = "Objek: Belum ada object terdeteksi";
      box.image.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=";
      box.colorName.textContent = "Warna: Tidak ada warna terdeteksi";
      box.colorCode.textContent = "Kode: Tidak ada kode warna terdeteksi";
      box.colorCode.style.color = "#1F2937";
      if (box.colorBox) {
        box.colorBox.style.backgroundColor = "#E5E7EB";
      }
    }
  });
}