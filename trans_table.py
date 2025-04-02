import pickle
import numpy as np
from typing import Dict, Tuple
from pygame_chess_api.api import Pawn, Queen, Knight, Bishop, Rook, King
import os
import time

class TranspositionTable:
    def __init__(self):
        self.table: Dict[int, Tuple[float, int, float]] = {}  # hash -> (value, visits, time_stamp)
        self.zobrist_table = self._initialize_zobrist_table()
        self.load_table()
        self.modified = False

    def _initialize_zobrist_table(self):
        # Khởi tạo bảng Zobrist cho mỗi quân cờ ở mỗi vị trí
        # 6 loại quân cờ * 2 màu * 64 ô cờ
        rng = np.random.default_rng(42)  # Sử dụng seed cố định
        return rng.integers(low=0, high=2**64, size=(6, 2, 8, 8), dtype=np.uint64)

    def get_piece_index(self, piece) -> int:
        # Chuyển đổi loại quân cờ thành index
        if isinstance(piece, Pawn): return 0
        elif isinstance(piece, Knight): return 1
        elif isinstance(piece, Bishop): return 2
        elif isinstance(piece, Rook): return 3
        elif isinstance(piece, Queen): return 4
        else: return 5  # King

    def compute_hash(self, board) -> int:
        h = 0
        for pos, piece in board.pieces_by_pos.items():
            x, y = pos
            piece_idx = self.get_piece_index(piece)
            h ^= self.zobrist_table[piece_idx][piece.color][x][y]
        return h

    def store(self, board_hash: int, value: float, visits: int):
        current_time = time.time()
        if board_hash in self.table:
            old_value, old_visits, old_time = self.table[board_hash]
            # Cập nhật nếu:
            # 1. Có nhiều lượt thăm hơn
            # 2. Hoặc có giá trị tốt hơn (cao hơn)
            # 3. Hoặc entry cũ đã quá cũ (>1 giờ)
            if visits > old_visits or value > old_value or current_time - old_time > 3600:
                self.table[board_hash] = (value, visits, current_time)
                self.modified = True
        else:
            self.table[board_hash] = (value, visits, current_time)
            self.modified = True

    def lookup(self, board_hash: int) -> Tuple[float, int]:
        if board_hash in self.table:
            value, visits, _ = self.table[board_hash]
            return value, visits
        return 0, 0

    def save_table(self):
        if self.modified:  # Chỉ lưu khi có thay đổi
            try:
                with open('transposition_table.pkl', 'wb') as f:
                    pickle.dump(self.table, f)
                self.modified = False
                print("Đã lưu transposition table")
            except Exception as e:
                print(f"Lỗi khi lưu transposition table: {e}")

    def load_table(self):
        try:
            if os.path.exists('transposition_table.pkl'):
                with open('transposition_table.pkl', 'rb') as f:
                    self.table = pickle.load(f)
                print(f"Đã tải transposition table với {len(self.table)} entries")
            else:
                self.table = {}
        except Exception as e:
            print(f"Lỗi khi tải transposition table: {e}")
            self.table = {}

    def cleanup_old_entries(self, max_age_hours=24):
        current_time = time.time()
        old_entries = []
        for board_hash, (value, visits, timestamp) in self.table.items():
            if current_time - timestamp > max_age_hours * 3600:
                old_entries.append(board_hash)
        
        for board_hash in old_entries:
            del self.table[board_hash]
        
        if old_entries:
            self.modified = True
            print(f"Đã xóa {len(old_entries)} entries cũ")

    def merge_from_worker(self, worker_results: Dict[int, Tuple[float, int, float]]):
        """Merge kết quả từ worker vào bảng chính"""
        current_time = time.time()
        updates = 0
        for board_hash, (value, visits, timestamp) in worker_results.items():
            if board_hash in self.table:
                old_value, old_visits, _ = self.table[board_hash]
                # Cập nhật nếu:
                # 1. Có nhiều lượt thăm hơn
                # 2. Hoặc có giá trị tốt hơn
                if visits > old_visits or value > old_value:
                    self.table[board_hash] = (value, visits, current_time)
                    self.modified = True
                    updates += 1
            else:
                self.table[board_hash] = (value, visits, current_time)
                self.modified = True
                updates += 1
        
        if updates > 0:
            print(f"Đã cập nhật {updates} entries mới/tốt hơn")

# Khởi tạo TranspositionTable như một biến toàn cục
TTABLE = TranspositionTable()