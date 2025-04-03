import hashlib
import time
import pickle
import os


class TranspositionTable:
    def __init__(self):
        self.table = {}  # Lưu trạng thái đã tính toán

    def save_table(self, file_path="trans_table.pkl"):
        try:
            with open(file_path, "wb") as f:
                pickle.dump(self.table, f)
            print(f"✅ Bảng băm đã được lưu ({len(self.table)} entries).")
        except Exception as e:
            print(f"⚠️ Lỗi khi lưu bảng băm: {e}")

    def load_table(self, file_path="trans_table.pkl"):
        """Tải bảng băm từ file nếu tồn tại."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    self.table = pickle.load(f)
                print(f"✅ Đã tải bảng băm ({len(self.table)} entries).")
            except Exception as e:
                print(f"⚠️ Lỗi khi tải bảng băm: {e}")

    def compute_hash(self, state):
        """Tạo hash duy nhất cho trạng thái bàn cờ."""
        board_str = str(state)  # Chuyển bàn cờ thành chuỗi để băm
        return hashlib.md5(board_str.encode()).hexdigest()

    def lookup(self, state):
        """Tìm trạng thái trong bảng băm."""
        board_hash = self.compute_hash(state)
        return self.table.get(board_hash, None)

    def store(self, state, value, visits):
        """Lưu trạng thái vào bảng băm."""
        board_hash = self.compute_hash(state)
        self.table[board_hash] = (value, visits, time.time())  # Lưu thời gian để dọn dẹp sau

    def cleanup_old_entries(self, max_age=300):
        """Xóa trạng thái cũ để tiết kiệm bộ nhớ (mặc định là 5 phút)."""
        current_time = time.time()
        self.table = {k: v for k, v in self.table.items() if current_time - v[2] < max_age}


# Khởi tạo bảng băm toàn cục
TTABLE = TranspositionTable()
