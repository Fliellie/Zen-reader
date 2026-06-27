import os
import json
import re
import sys
import webview
import pypdf

# ==========================================================================
# ⚙️ CẤU HÌNH ĐƯỜNG DẪN TUYỆT ĐỐI (Fix lỗi khi đóng gói .exe)
# ==========================================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKING_DIR = os.getcwd()
TXT_FOLDER = os.path.join(WORKING_DIR, "extracted_books")  
DATA_FILE = os.path.join(WORKING_DIR, "library.json")      

if not os.path.exists(TXT_FOLDER):
    os.makedirs(TXT_FOLDER)


# ==========================================================================
# 🗄️ CẦU NỐI API GIỮA JAVASCRIPT VÀ PYTHON (Tất cả hàm gom tại đây)
# ==========================================================================
class ReadingAppBridge:
    def __init__(self):
        self.active_book_id = ""

    # --- 1. Quản lý Tủ Sách ---
    def get_library(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def set_active_book(self, book_id):
        self.active_book_id = book_id
        return True

    def get_active_book(self):
        return self.active_book_id

    def save_progress(self, book_id, current_index):
        library = self.get_library()
        if book_id in library:
            library[book_id]["current_index"] = int(current_index)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)
            return {"status": "saved"}
        return {"status": "not_found"}

    # --- 2. Điều hướng giao diện HTML ---
    def switch_to_reader(self):
        read_html_path = os.path.join(BASE_DIR, 'templates', 'read.html')
        webview.windows[0].load_url(read_html_path)
        return True

    def switch_to_home(self):
        index_html_path = os.path.join(BASE_DIR, 'templates', 'index.html')
        webview.windows[0].load_url(index_html_path)
        return True

    # --- 3. Tính năng Trích xuất File PDF ---
    def open_pdf_dialog(self):
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
                
            return {"status": "success", "library": library, "new_book_id": book_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- 4. Tính năng Đọc Sách từng câu ---
    def load_book_sentences(self, book_id):
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

# --- 5. Tính năng Cào và Dịch phụ đề YouTube ---
    def create_book_from_youtube(self, youtube_url, user_lang):
        """Tải phụ đề YouTube theo chuẩn tài liệu fetch(), tự động dịch và lưu thành sách"""
        import os
        import json
        import re
        from deep_translator import GoogleTranslator
        
        # Đảm bảo thư mục lưu sách 'extracted_books' luôn tồn tại
        extracted_books = "extracted_books" 
        if not os.path.exists(extracted_books):
            os.makedirs(extracted_books)

        # Sử dụng đúng file danh mục của dự án (thường là library.json hoặc data.json)
        DATA_FILE_NAME = "library.json"

        try:
            # 1. Trích xuất Video ID từ URL bằng Regex
            video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
            if not video_id_match:
                return {"status": "error", "message": "Đường dẫn YouTube không hợp lệ!"}
            video_id = video_id_match.group(1)

            # 2. Bốc phụ đề chuẩn theo thuộc tính đối tượng (.text)
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                ytt_api = YouTubeTranscriptApi()
                transcript_data = ytt_api.fetch(video_id)
                
                # Gộp dữ liệu thông qua thuộc tính đối tượng .text (sửa lỗi 'not subscriptable')
                full_text = " ".join([entry.text for entry in transcript_data])
                video_title = f"YouTube_{video_id}"

            except Exception as e:
                return {"status": "error", "message": f"Không lấy được phụ đề từ API YouTube! Chi tiết: {str(e)}"}

            # 3. Logic Dịch tự động qua Google dịch (nếu người dùng chọn dịch sang 'vi')
            text_content = full_text
            if user_lang == 'vi':
                translator = GoogleTranslator(source='en', target='vi')
                words = full_text.split()
                chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
                translated_chunks = [translator.translate(chunk) for chunk in chunks]
                text_content = " ".join(translated_chunks)

            text_content = re.sub(r'\s+', ' ', text_content).strip()

            # 4. Đăng ký sách vào hệ thống file txt và thư viện JSON
            book_id = f"yt_{video_id}"
            txt_filename = f"{book_id}.txt"
            
            # Khớp hoàn toàn với biến 'extracted_books' trong ảnh chụp của bạn
            txt_filepath = os.path.join(extracted_books, txt_filename)
            
            # Ghi file nội dung sách
            with open(txt_filepath, "w", encoding="utf-8") as f:
                f.write(text_content)

            # Đọc và cập nhật file quản lý danh sách sách
            library = {}
            if os.path.exists(DATA_FILE_NAME):
                try:
                    with open(DATA_FILE_NAME, "r", encoding="utf-8") as f:
                        library = json.load(f)
                except:
                    library = {}

            library[book_id] = {
                "title": f"[YouTube] {video_title}",
                "original_path": youtube_url,
                "txt_path": txt_filepath,
                "current_index": 0
            }

            with open(DATA_FILE_NAME, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)

            return {"status": "success", "library": library, "new_book_id": book_id}

        except Exception as e:
            return {"status": "error", "message": f"Hệ thống gặp lỗi: {str(e)}"}
# ==========================================================================
# 🚀 KHỞI CHẠY ỨNG DỤNG
# ==========================================================================
if __name__ == '__main__':
    bridge = ReadingAppBridge()
    start_html_path = os.path.join(BASE_DIR, 'templates', 'index.html')
    
    window = webview.create_window(
        'Pixel Zen Reader', 
        start_html_path, 
        js_api=bridge,
        width=1000,
        height=650,
        resizable=True
    )
    webview.start()