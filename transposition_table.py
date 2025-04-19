import chess
from typing import NamedTuple, Optional, Dict


# Định nghĩa các loại Node
class NodeType:
    EXACT = 0
    LOWER_BOUND = 1
    UPPER_BOUND = 2


class TTEntry(NamedTuple):
    depth: int
    score: int
    node_type: int
    best_move: Optional[chess.Move]


class TranspositionTable:
    def __init__(self, size_mb=64):
        self.table: Dict[int, TTEntry] = {}

    def probe(self, zobrist_key, depth, alpha, beta):
        """
        Thăm dò bảng TT
        :param zobrist_key: zorbist_key
        :param depth: độ sâu
        :param alpha: alpha
        :param beta: beta
        :return: (score, best_move) nếu tìm thấy mục hợp lệ và có thể gây cắt tỉa
        hoặc trả về điểm chính xác
            Trả về None nếu không tìm thấy hoặc không đủ sâu.
        """
        entry = self.table.get(zobrist_key)
        if entry is None:
            return None
        if entry.depth < depth:
            return None
        if entry.node_type == NodeType.EXACT:
            return entry.score, entry.best_move
        if entry.node_type == NodeType.LOWER_BOUND:
            if entry.score >= beta:
                return entry.score, entry.best_move
        if entry.node_type == NodeType.UPPER_BOUND:
            if entry.score <= alpha:
                return entry.score, entry.best_move
        return None

    def store(self, zobrist_key, depth, score, node_type, best_move):
        """
        Lưu trữ hoặc cập nhật một mục trong TT
        :param zobrist_key: zorbist_key
        :param depth: độ sâu
        :param score: điểm đánh giá
        :param node_type: loại node
        :param best_move: nước đi tốt nhất
        """
        existing_entry = self.table.get(zobrist_key)
        if existing_entry is None or depth >= existing_entry.depth:
            new_entry = TTEntry(depth, score, node_type, best_move)
            self.table[zobrist_key] = new_entry

    def get_pv_move(self, zobrist_key):
        """
        Lấy nước đi PV (nếu có) từ TT mà không cần kiểm tra độ sâu.
        :param zobrist_key: zorbist_key
        :return: Nước đi tốt nhất (nếu có)
        """
        entry = self.table.get(zobrist_key)
        if entry:
            return entry.best_move
        return None

    def clear(self):
        """
        Xóa bảng TT
        """
        self.table.clear()

    def __len__(self):
        """
        Độ dài bảng
        :return: Độ dài bảng
        """
        return len(self.table)
