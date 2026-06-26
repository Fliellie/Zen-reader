import os
import json
import re
import sys
import webview
import pypdf

# ==========================================================================
# CẤU HÌNH ĐƯỜNG DẪN THỰC TẾ TRÊN Ổ ĐĨA
# ==========================================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# library.json và extracted_books sẽ nằm cùng nơi với file .exe hoặc file app.py chạy chính
WORKING_DIR = os.getcwd()
STORAGE_DIR = os.path.join(WORKING_DIR, "extracted_books")
DATA_FILE = os.path.join(WORKING_DIR, "library.json")

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

class LibraryBridge:
    def __init__(self):
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

    def switch_to_reader(self):
        """Hàm chuyển sang màn hình đọc (read.html) mà không cần server"""
        read_html_path = os.path.join(BASE_DIR, 'templates', 'read.html')
        webview.windows[0].load_url(read_html_path)
        return True
        
    def switch_to_home(self):
        """Hàm quay lại màn hình tủ sách (index.html)"""
        index_html_path = os.path.join(BASE_DIR, 'templates', 'index.html')
        webview.windows[0].load_url(index_html_path)
        return True


if __name__ == '__main__':
    index_html_path = os.path.join(BASE_DIR, 'templates', 'index.html')

    bridge = LibraryBridge()
    
    window = webview.create_window(
        'Pixel Zen Reader', 
        index_html_path,  
        js_api=bridge,
        width=1000,
        height=650,
        resizable=True
    )
    webview.start()