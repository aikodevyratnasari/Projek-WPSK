const mainFrameImage = document.getElementById("mainFrameImage");
const detectionBoxes = [1, 2, 3, 4, 5, 6].map((i) => ({
  container: document.getElementById(`detection-box-${i}`),
  label: document.getElementById(`label-${i}`),
  image: document.getElementById(`image-${i}`),
  colorName: document.getElementById(`color-name-${i}`),
  colorCode: document.getElementById(`color-code-${i}`),
  colorBox: document.getElementById(`color_box_${i}`), // Menambahkan referensi ke elemen kotak warna
}));

// Inisialisasi placeholder image dan kotak warna default
detectionBoxes.forEach((box) => {
  box.image.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="; // Transparent 1x1 GIF
  if (box.colorBox) {
    box.colorBox.style.backgroundColor = "#E5E7EB"; // Warna default abu-abu muda
  }
});

const socket = new WebSocket("ws://localhost:1234"); // Perhatikan 'ws://'

socket.onmessage = function (event) {
  try {
    const data = JSON.parse(event.data); // Data adalah JSON

    // Update Main Frame Image
    if (data.full_frame_base64) {
      mainFrameImage.src = "data:image/jpeg;base64," + data.full_frame_base64;
    }

    // Update Detection Boxes
    detectionBoxes.forEach((box, index) => {
      if (data.detections && data.detections[index]) {
        const detection = data.detections[index];
        box.label.textContent = `Objek: ${detection.label}`;
        box.image.src = `data:image/jpeg;base64,${detection.cropped_image_base64}`;
        box.colorName.textContent = `Warna: ${detection.color_name}`;
        box.colorCode.textContent = `Kode: ${detection.color_code}`;
        box.colorCode.style.color = "#1F2937"; // Teks kode warna tetap hitam (dark gray Tailwind)

        // Update warna kotak warna
        if (box.colorBox) {
          box.colorBox.style.backgroundColor = detection.color_code;
        }
      } else {
        // Reset atau tampilkan placeholder jika tidak ada deteksi untuk kotak ini
        box.label.textContent = "Objek: Belum ada object terdeteksi";
        box.image.src =
          "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=";
        box.colorName.textContent = "Warna: Tidak ada warna terdeteksi";
        box.colorCode.textContent = "Kode: Tidak ada kode warna terdeteksi";
        box.colorCode.style.color = "#1F2937"; // Pastikan teks kode warna default hitam
        if (box.colorBox) {
          box.colorBox.style.backgroundColor = "#E5E7EB"; // Reset ke default abu-abu muda
        }
      }
    });
  } catch (e) {
    console.error("Failed to parse JSON or update elements:", e, event.data);
  }
};

socket.onopen = () => {
  console.log("Connected to WebSocket server");
};

socket.onclose = () => {
  console.log("Disconnected from WebSocket server");
};

socket.onerror = (error) => {
  console.error("WebSocket error:", error);
};
