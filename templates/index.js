// ==========================================================================
// 💡 PHẦN 1: CÁC CHIẾC HỘP GHI NHỚ (BIẾN TOÀN CỤC)
// Giống như ba mẩu giấy nhớ dán trên bàn làm việc để nhân viên luôn biết:
// Đang mở cuốn nào? Nội dung có những câu gì? Và đang đọc tới dòng mấy?
// ==========================================================================

// Biến toàn cục để lưu trữ thông tin cuốn sách đang đọc
let currentBookId = "";      // Lưu "Mã định danh" (ID) của cuốn sách hiện tại
let currentSentences = [];   // Lưu "Danh sách tất cả các câu" có trong cuốn sách đó
let currentIndex = 0;        // Lưu "Vị trí câu" mà người dùng đang đọc (bắt đầu từ câu số 0)

// ==========================================================================
// 💡 PHẦN 2: KHỞI ĐỘNG ỨNG DỤNG
// Khi ứng dụng mở lên, nó cần một chút thời gian để kết nối với "Kho Python".
// Đoạn này dặn máy: "Khi nào kết nối xong xuôi thì tự động đi dọn kệ sách nhé!"
// ==========================================================================

// 1. Chờ cho đến khi PyWebView nạp xong xuôi API từ Python
window.addEventListener('pywebviewready', function() {
    loadLibrary(); // Cửa sổ sẵn sàng là gọi hàm bốc sách xếp lên kệ ngay
});

// ==========================================================================
// 💡 PHẦN 3: QUẢN LÝ "TỦ SÁCH" (HIỂN THỊ DANH SÁCH)
// Hàm này có nhiệm vụ: Vào kho Python lấy hết sách ra, vẽ thành các ô vuông 
// (Card) đẹp đẽ trên màn hình. Nếu không có sách thì hiện thông báo trống.
// ==========================================================================

// 2. Hàm lấy danh sách sách từ Python và hiển thị lên các ô chữ nhật (Grid)
async function loadLibrary() {
    // Lấy 2 khu vực trên giao diện bằng ID của chúng
    const booksGrid = document.getElementById('books-grid'); // Vùng chứa các ô sách
    const emptyState = document.getElementById('empty-state'); // Vùng hiện chữ "Chưa có sách"
    
    // Gọi Python: "Cho xin danh sách sách trong kho" (await là chờ Python trả lời)
    const library = await pywebview.api.get_library();
    // Lấy ra danh sách các mã ID của sách
    const bookIds = Object.keys(library);
    
    // NẾU TRONG KHO KHÔNG CÓ CUỐN SÁCH NÀO:
    if (bookIds.length === 0) {
        emptyState.style.display = 'block'; // Hiện thông báo "Tủ sách trống"
        removeOldCards(booksGrid);          // Xóa các ô sách cũ (nếu có)
        return;                             // Dừng hàm ở đây, không làm tiếp bên dưới
    }
    
    // NẾU CÓ SÁCH TRONG KHO:
    emptyState.style.display = 'none'; // Ẩn thông báo trống đi
    removeOldCards(booksGrid);         // Dọn dẹp các ô sách cũ để xếp loạt mới lên
    
    // Duyệt qua từng mã sách để vẽ "tấm card" cho cuốn sách đó
    // Thay thế đoạn vòng lặp bookIds.forEach(id => { ... }) cũ bằng đoạn này:
bookIds.forEach(id => {
    const book = library[id]; // Lấy thông tin chi tiết (Tiêu đề, tiến độ...)
    const card = document.createElement('div'); // Tạo một ô vuông mới
    card.className = 'book-card'; // Đặt tên lớp là 'book-card'
    
    // Bỏ chữ, thông tin tiến độ và THÊM CỤM NÚT ĐIỀU KHIỂN (Đọc tiếp & Xóa)
    card.innerHTML = `
        <div class="book-title">${book.title}</div>
        <div class="book-progress">Dòng hiện tại: ${book.current_index}</div>
        <div class="book-actions" style="display: flex; gap: 8px; margin-top: 10px;">
            <button class="btn-pixel btn-read-now" onclick="startReading('${id}')" style="flex: 1;">ĐỌC TIẾP</button>
            <button class="btn-pixel btn-delete" onclick="deleteBook('${id}', '${book.title.replace(/'/g, "\\'")}')" style="background-color: #ff4d4d; color: white;">XÓA</button>
        </div>
    `;
    booksGrid.appendChild(card); // Thêm ô vuông vào vùng hiển thị
});
}

// Hàm phụ: Giống như việc quét dọn kệ sách cũ, xóa hết các ô chữ nhật cũ đi để tránh bị trùng lặp
function removeOldCards(container) {
    const cards = container.querySelectorAll('.book-card');
    cards.forEach(card => card.remove()); // Duyệt qua từng cái card cũ và xóa bỏ
}

// ==========================================================================
// 💡 PHẦN 4: NÚT THÊM SÁCH (TẢI FILE PDF LÊN)
// Khi bấm nút "Mở file PDF", nút này sẽ đổi chữ thành "Đang đọc file..." và đóng băng
// không cho bấm tiếp (để tránh người dùng bấm lia lịa gây lỗi). Xử lý xong thì mở lại.
// ==========================================================================

// 3. Hàm kích hoạt khi người dùng bấm nút "MỞ FILE PDF" ở thanh bên trái
async function triggerUploadPDF() {
    const btn = document.getElementById('btn-upload');
    btn.innerText = "ĐANG ĐỌC FILE..."; // Đổi chữ nút bấm thành thông báo đang xử lý
    btn.style.pointerEvents = "none";  // Khóa nút bấm lại, bấm vào không có tác dụng nữa
    
    // Gọi Python mở hộp thoại chọn file PDF trên máy tính và chờ kết quả
    const result = await pywebview.api.open_pdf_dialog();
    
    btn.innerText = "MỞ FILE PDF";     // Trả lại tên cũ cho nút bấm
    btn.style.pointerEvents = "auto";   // Mở khóa nút bấm, người dùng có thể bấm lại bình thường
    
    // Kiểm tra xem Python xử lý file thành công hay thất bại
    if (result.status === 'success') {
        loadLibrary(); // Thành công thì load lại tủ sách để thấy cuốn sách mới xuất hiện
    } else if (result.status === 'error') {
        alert("Có lỗi xảy ra khi xử lý file PDF: " + result.message); // Thất bại thì hiện bảng báo lỗi
    }
}

// ==========================================================================
// CHỨC NĂNG MỚI: CHUYỂN SANG GIAO DIỆN ĐỌC (READ ROOM)
// ==========================================================================

// ==========================================================================
// 💡 PHẦN 5: VÀO PHÒNG ĐỌC SÁCH
// Khi người dùng click "ĐỌC TIẾP" ở một cuốn sách, hàm này sẽ cất Tủ sách đi,
// lôi cuốn sách đó ra, chuẩn bị nội dung và mở giao diện đọc sách lên.
// ==========================================================================

// Hàm xử lý khi người dùng bấm vào nút "ĐỌC TIẾP" của một cuốn sách
async function startReading(bookId) {
    // 1. Gửi bookId xuống Python để Python ghi nhớ cuốn sách đang được kích hoạt
    await pywebview.api.set_active_book(bookId);
    
    // 2. CHUYỂN TRANG: Ra lệnh cho cửa sổ app load file HTML mới (read.html)
    window.location.href = "read.html";
}

// ==========================================================================
// 💡 PHẦN 6: IN CHỮ LÊN MÀN HÌNH ĐỌC
// Nhiệm vụ rất đơn giản: Nhìn vào "mẩu giấy nhớ" xem đang ở câu mấy, lấy câu đó
// dán lên màn hình kèm theo cái tiến độ (Ví dụ: [ DÒNG: 5 / 100 ])
// ==========================================================================

// Hàm hiển thị câu và tiến độ số câu
function renderSentence() {
    const textDisplay = document.getElementById("sentence-display");
    // Lấy câu thứ [currentIndex] trong mảng ra để hiển thị lên màn hình
    textDisplay.innerText = currentSentences[currentIndex];
    
    // Hiển thị tiến độ kiểu pixel (Ví dụ: [ 42 / 1200 ])
    const progressText = document.getElementById("reading-progress-text");
    // Số thứ tự hiển thị với người dùng sẽ bằng chỉ số trong code cộng thêm 1 (vì code đếm từ số 0)
    progressText.innerText = `[ DÒNG: ${currentIndex + 1} / ${currentSentences.length} ]`;
}

// ==========================================================================
// 💡 PHẦN 7: QUAY LẠI TỦ SÁCH
// Khi người dùng chán đọc, bấm nút "Thoát": Hàm này sẽ ẩn màn hình đọc,
// bật lại tủ sách, đồng thời cập nhật lại tiến độ mới nhất của cuốn sách ra ngoài.
// ==========================================================================

// Hàm quay lại Tủ Sách
function backToLibrary() {
    // Nạp lại tủ sách để cập nhật tiến độ mới nhất lên các ô chữ nhật
    loadLibrary();
    
    // CHUYỂN GIAO DIỆN: Hiện Tủ Sách (flex), Ẩn Màn Hình Đọc (none)
    document.getElementById("main-library-view").style.display = "flex";
    document.getElementById("main-reader-view").style.display = "none";
}
// đây là index.js
// hàm dùng để xử lí phần tạo sách từ video trên youtube
// đầu tiên mở 1 của sổ mới đè lên index.html
// trong cửa sổ hỏi người dùng nhập link video youtube
// chọn ngôn ngữ [Anh, việt]- tức là bạn là người anh hay việt
// nhấn oke để bắt đầu quá trình
// gửi yêu cầu cho file app.py
// Ví dụ khi người dùng nhấn nút khởi chạy trong popup nhập liệu
function handleCreateYoutubeBook() {
    document.getElementById('youtube-modal').style.display = 'flex';
}
// 2. Hàm đóng cửa sổ popup khi người dùng bấm Hủy
function closeYoutubeModal() {
    document.getElementById('youtube-modal').style.display = 'none';
    document.getElementById('youtube-link-input').value = ""; // Xóa text cũ đi
}

// 3. Hàm kích hoạt khi người dùng nhấn nút "BẮT ĐẦU" trong popup
async function submitYoutubeRequest() {
    const youtubeUrl = document.getElementById('youtube-link-input').value; 
    const userLang = document.getElementById('lang-select').value; 
    const btnConfirm = document.querySelector('.btn-confirm');

    if (!youtubeUrl) {
        alert("Vui lòng nhập link YouTube!");
        return;
    }

    // Đóng băng nút bấm tạm thời để tránh bấm nhiều lần
    btnConfirm.innerText = "ĐANG XỬ LÝ...";
    btnConfirm.style.pointerEvents = "none";

    try {
        // Gửi yêu cầu xuống Python xử lý ngầm
        const response = await pywebview.api.create_book_from_youtube(youtubeUrl, userLang);
        
        if (response.status === "success") {
            alert("Tạo sách từ YouTube thành công!");
            closeYoutubeModal();
            loadLibrary(); // Tải lại tủ sách để thấy cuốn sách YouTube xuất hiện
        } else {
            alert("Lỗi: " + response.message);
        }
    } catch (err) {
        alert("Lỗi kết nối Python: " + err);
    } finally {
        // Mở khóa lại nút bấm
        btnConfirm.innerText = "BẮT ĐẦU";
        btnConfirm.style.pointerEvents = "auto";
    }
}
// ==========================================================================
// CHỨC NĂNG MỚI: XÓA SÁCH KHỎI THƯ VIỆN
// ==========================================================================
async function deleteBook(bookId, bookTitle) {
    // Hiện bảng hỏi xác nhận kiểu cổ điển (Confirm Dialog)
    const confirmDelete = confirm(`Bạn có chắc chắn muốn xóa cuốn sách "${bookTitle}" không?\nHành động này không thể hoàn tác!`);
    
    if (confirmDelete) {
        try {
            // Gọi hàm delete_book dưới Python (tí nữa bạn sẽ thêm hàm này vào app.py)
            const response = await pywebview.api.delete_book(bookId);
            
            if (response.status === 'success') {
                alert("Đã xóa sách thành công!");
                loadLibrary(); // Xóa xong xuôi thì vẽ lại thư viện mới
            } else {
                alert("Lỗi khi xóa sách: " + response.message);
            }
        } catch (err) {
            alert("Lỗi kết nối Python khi xóa: " + err);
        }
    }
}