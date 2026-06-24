import os
import json
import re
import webview
import pypdf

# 1. Tự động tạo thư mục lưu trữ sách nếu chưa có
STORAGE_DIR = "extracted_books"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

DATA_FILE = "library.json"

class LibraryBridge:
    def __init__(self):
        # Biến bộ nhớ tạm để ghi nhớ ID cuốn sách người dùng chọn "ĐỌC TIẾP"
        self.active_book_id = ""

    def get_library(self):
        """Đọc danh sách các sách và tiến độ đọc từ file JSON cục bộ"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def open_pdf_dialog(self):
        """Mở hộp thoại chọn file PDF, chuyển thành text và lưu local"""
        file_types = ('PDF Files (*.pdf)',)
        file_path = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG, file_types=file_types)
        
        if not file_path:
            return {"status": "cancelled"}
            
        path = file_path[0]
        filename = os.path.basename(path)
        book_id = re.sub(r'[^a-zA-Z0-9]', '_', filename.replace(".pdf", ""))
        
        try:
            text_content = ""
            reader = pypdf.PdfReader(path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content += text + " "
            
            # Làm sạch khoảng trắng thừa giúp thuật toán cắt câu chuẩn hơn
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            txt_filename = f"{book_id}.txt"
            txt_filepath = os.path.join(STORAGE_DIR, txt_filename)
            with open(txt_filepath, "w", encoding="utf-8") as f:
                f.write(text_content)
            
            library = self.get_library()
            if book_id not in library:
                library[book_id] = {
                    "title": filename.replace(".pdf", ""),
                    "original_path": path,
                    "txt_path": txt_filepath,
                    "current_index": 0  
                }
            
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)
                
            return {"status": "success", "library": library, "new_book_id": book_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ==========================================================================
    # CÁC HÀM BỔ SUNG ĐỂ KẾT NỐI VỚI read.html VÀ read.js
    # ==========================================================================

    def set_active_book(self, book_id):
        """Ghi nhớ sách đang được chọn để đọc"""
        self.active_book_id = book_id
        return True

    def get_active_book(self):
        """Trả về ID sách đang đọc cho màn hình read.html nhận diện khi vừa load"""
        return self.active_book_id

    def load_book_sentences(self, book_id):
        """Đọc file .txt và băm nhỏ thành mảng các câu gửi lên giao diện đọc"""
        library = self.get_library()
        if book_id not in library:
            return {"status": "error", "message": "Không tìm thấy sách trong tủ sách!"}
            
        book_info = library[book_id]
        txt_path = book_info["txt_path"]
        
        if not os.path.exists(txt_path):
            return {"status": "error", "message": "File văn bản (.txt) đã bị xóa mất!"}
            
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Cắt câu bằng dấu chấm, hỏi, than
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
        """Cập nhật dòng đang đọc khi bấm Next/Back"""
        library = self.get_library()
        if book_id in library:
            library[book_id]["current_index"] = int(current_index)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)
            return {"status": "saved"}
        return {"status": "not_found"}


if __name__ == '__main__':
    bridge = LibraryBridge()
    
    window = webview.create_window(
        'Pixel Zen Reader', 
        'templates/index.html', 
        js_api=bridge,
        width=1000,
        height=650,
        resizable=True
    )
    webview.start()