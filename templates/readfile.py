import os
import json
import re
import webview
import pypdf

TXT_FOLDER = "extracted_books"  
DATA_FILE = "library.json"      

if not os.path.exists(TXT_FOLDER):
    os.makedirs(TXT_FOLDER)

class ReadingAppBridge:
    def __init__(self):
        # Biến bộ nhớ tạm dùng để ghi nhớ ID cuốn sách người dùng vừa ấn "ĐỌC TIẾP"
        self.active_book_id = ""

    def get_library(self):
        """Đọc và trả về danh sách sách từ file library.json cho JS hiển thị"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def open_pdf_dialog(self):
        """Mở hộp thoại chọn file PDF -> Chuyển sang TXT -> Lưu thông tin local"""
        file_types = ('PDF Files (*.pdf)',)
        file_path = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG, file_types=file_types)
        
        if not file_path:
            return {"status": "cancelled"}
            
        selected_path = file_path[0]
        filename = os.path.basename(selected_path)
        book_id = re.sub(r'[^a-zA-Z0-9]', '_', filename.replace(".pdf", ""))
        
        try:
            text_content = ""
            reader = pypdf.PdfReader(selected_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content += text + " "
            
            # Xóa các khoảng trắng thừa, dồn dòng lỗi của PDF lại thành một mạch chữ liền
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            txt_filename = f"{book_id}.txt"
            txt_filepath = os.path.join(TXT_FOLDER, txt_filename)
            with open(txt_filepath, "w", encoding="utf-8") as f:
                f.write(text_content)
            
            library = self.get_library()
            library[book_id] = {
                "title": filename.replace(".pdf", ""),
                "original_path": selected_path,
                "txt_path": txt_filepath,
                "current_index": 0 
            }
            
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)
                
            return {"status": "success", "library": library}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ==========================================================================
    # CÁC HÀM MỚI BỔ SUNG ĐỂ SỬA LỖI CHUYỂN TRANG
    # ==========================================================================

    def set_active_book(self, book_id):
        """Nhận lệnh từ index.js để ghi nhớ cuốn sách sắp đọc trước khi đổi trang"""
        self.active_book_id = book_id
        return True

    def get_active_book(self):
        """Trả về ID cuốn sách đang đọc cho màn hình read.html nhận diện khi vừa load xong"""
        return self.active_book_id

    def load_book_sentences(self, book_id):
        """Đọc file .txt tương ứng và băm nhỏ thành mảng các câu để gửi lên màn hình đọc"""
        library = self.get_library()
        if book_id not in library:
            return {"status": "error", "message": "Không tìm thấy sách trong tủ sách!"}
            
        book_info = library[book_id]
        txt_path = book_info["txt_path"]
        
        if not os.path.exists(txt_path):
            return {"status": "error", "message": "File văn bản của cuốn sách này đã bị mất trên ổ đĩa!"}
            
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Thuật toán cắt câu dựa vào các dấu kết thúc: ., ?, !
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            return {
                "status": "success",
                "title": book_info["title"],
                "sentences": sentences,
                "current_index": book_info["current_index"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def save_progress(self, book_id, current_index):
        """Lưu tiến độ dòng đang đọc dở mỗi khi người dùng bấm Next/Back"""
        library = self.get_library()
        if book_id in library:
            library[book_id]["current_index"] = int(current_index)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)
            return {"status": "saved"}
        return {"status": "not_found"}


if __name__ == '__main__':
    bridge = ReadingAppBridge()
    
    window = webview.create_window(
        'Pixel Zen Reader', 
        'templates/index.html', 
        js_api=bridge,
        width=1000,
        height=650,
        resizable=True
    )
    webview.start()