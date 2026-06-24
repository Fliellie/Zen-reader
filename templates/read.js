let sentences = [];
let currentIndex = 0;
let bookId = "";
let currentFontSize = 36; // Cỡ chữ khổng lồ mặc định ban đầu

// 1. Chờ PyWebView sẵn sàng thì bắt đầu tải dữ liệu sách
window.addEventListener('pywebviewready', async function() {
    // Lấy ID cuốn sách đang được chọn từ Python
    bookId = await pywebview.api.get_active_book();
    
    if (!bookId) {
        alert("Không tìm thấy thông tin sách!");
        goBackToLibrary();
        return;
    }

    // Tải danh sách câu và tiến độ của cuốn sách này
    const result = await pywebview.api.load_book_sentences(bookId);
    
    if (result.status === 'error') {
        alert(result.message);
        goBackToLibrary();
        return;
    }

    // Lưu vào biến local của trang read.html
    sentences = result.sentences;
    currentIndex = result.current_index;

    // Hiển thị tiêu đề sách
    document.getElementById("book-title-indicator").innerText = `📖 ${result.title}`;
    
    // Hiển thị câu hiện tại
    renderSentence();
});

// 2. Hàm hiển thị câu chữ lên màn hình
function renderSentence() {
    const box = document.getElementById("sentence-box");
    const counter = document.getElementById("sentence-counter");

    if (sentences.length === 0) {
        box.innerText = "Sách không có nội dung chữ.";
        return;
    }

    // Đảm bảo chỉ số không chạy ra ngoài mảng
    if (currentIndex >= sentences.length) currentIndex = sentences.length - 1;
    if (currentIndex < 0) currentIndex = 0;

    // Bơm câu hiện tại vào ô chữ nhật
    box.innerText = sentences[currentIndex];
    
    // Cập nhật số dòng đang đọc
    counter.innerText = `[ DÒNG: ${currentIndex + 1} / ${sentences.length} ]`;

    // Gửi lệnh xuống Python để lưu tiến độ tự động vào library.json
    pywebview.api.save_progress(bookId, currentIndex);
}

// 3. Hàm chuyển sang câu tiếp theo
function nextSentence() {
    if (currentIndex < sentences.length - 1) {
        currentIndex++;
        renderSentence();
    } else {
        alert("Chúc mừng! Bạn đã đọc hết cuốn sách này!");
    }
}

// 4. Hàm quay lại câu phía trước
function prevSentence() {
    if (currentIndex > 0) {
        currentIndex--;
        renderSentence();
    }
}

// 5. Hàm quay lại màn hình tủ sách chính
function goBackToLibrary() {
    window.location.href = "index.html";
}

// ==========================================================================
// CÁC TÍNH NĂNG NÂNG CẤP (FONT CHỮ, ĐỔI SIZE, TOGGLE THEME SWITCH)
// ==========================================================================

// Thay đổi phông chữ động từ Dropdown
function changeFont(fontName) {
    document.getElementById("sentence-box").style.fontFamily = fontName;
}

/**
 * TÍNH NĂNG MỚI: Tăng hoặc giảm cỡ chữ động (+ / -)
 * @param {number} offset - Số lượng pixel muốn tăng/giảm (ví dụ: 2 hoặc -2)
 */
function adjustFontSize(offset) {
    currentFontSize += offset;
    
    // Đặt giới hạn an toàn: chữ nhỏ nhất 18px, to nhất 72px để tránh vỡ khung
    if (currentFontSize < 18) currentFontSize = 18;
    if (currentFontSize > 72) currentFontSize = 72;
    
    // Thực thi thay đổi trực tiếp lên ô hiển thị chữ
    document.getElementById("sentence-box").style.fontSize = `${currentFontSize}px`;
}

/**
 * TÍNH NĂNG MỚI: Bật/Tắt chế độ Đêm bằng Switch Class
 * Đồng bộ đổi text hiển thị trên nút bấm tương ứng
 */
function toggleTheme() {
    const body = document.getElementById("zen-body");
    const toggleBtn = document.getElementById("theme-toggle-btn");
    
    // Kích hoạt hoặc gỡ bỏ class .dark-mode tại thẻ <body>
    body.classList.toggle("dark-mode");
    
    // Cập nhật nhãn hiển thị của nút bấm
    if (body.classList.contains("dark-mode")) {
        if (toggleBtn) toggleBtn.innerText = "☀️ SÁNG";
    } else {
        if (toggleBtn) toggleBtn.innerText = "👁 ĐÊM";
    }
}

// BẮT SỰ KIỆN PHÍM TẮT: Hỗ trợ phím Mũi tên, Enter để lướt nhanh hơn
document.addEventListener('keydown', function(event) {
    if (event.key === "ArrowRight" || event.key === "Enter" || event.key === " ") {
        event.preventDefault(); // Ngăn Spacebar/Enter cuộn trang lỗi
        nextSentence();
    } else if (event.key === "ArrowLeft") {
        prevSentence();
    }
});