import chess
from typing import Optional # Thêm Optional để gợi ý kiểu cho best_move

# Import các thành phần cần thiết từ các file khác
from config import * # Giả sử config chứa PIECE_VALUES nếu orders.py không định nghĩa lại
from evaluation import evaluate_position
from move_ordering import order_moves # <<<--- IMPORT HÀM SẮP XẾP

# --- Cấu trúc dữ liệu tạm thời (nếu chưa có) ---
# Nếu bạn chưa có cấu trúc quản lý search data (TT, Killers, History),
# bạn có thể dùng placeholder trước. Khi có, bạn sẽ truyền nó vào.
class DummySearchData:
    """Placeholder nếu chưa có cấu trúc dữ liệu search thực sự."""
    def __init__(self):
        self.transposition_table = None # Thay bằng TT thật sau
        self.killer_moves = {} # Ví dụ: dict dạng {ply: [move1, move2]}
        self.history_heuristic_table = {} # Ví dụ: dict dạng {(from, to): score}

    def get_killer_moves(self, ply):
        # Trả về cặp killer moves cho ply hiện tại (có thể là None)
        return self.killer_moves.get(ply, (None, None))

    def store_killer_move(self, ply, move):
        # Logic lưu trữ killer move (ví dụ: đẩy move mới vào, bỏ move cũ)
        if ply not in self.killer_moves:
            self.killer_moves[ply] = [None, None]
        if move != self.killer_moves[ply][0]: # Tránh trùng lặp
            self.killer_moves[ply][1] = self.killer_moves[ply][0]
            self.killer_moves[ply][0] = move

    def update_history_score(self, move, depth):
        # Logic cập nhật điểm history (ví dụ: tăng điểm cho nước đi gây cắt tỉa)
        key = (move.from_square, move.to_square)
        self.history_heuristic_table[key] = self.history_heuristic_table.get(key, 0) + depth * depth

# Khởi tạo đối tượng search data (tạm thời)
search_data = DummySearchData()
# ----------------------------------------------------


def negamax(board_: chess.Board, depth_: int, alpha: float, beta: float, color: int, ply: int): # <<< Thêm tham số ply
    """
    Negamax với cắt tỉa Alpha-Beta và sắp xếp nước đi.
    :param board_: bàn cờ
    :param depth_: độ sâu còn lại
    :param alpha: alpha
    :param beta: beta
    :param color: 1 cho trắng, -1 cho đen
    :param ply: Độ sâu hiện tại từ gốc (dùng cho killers/history)
    :return: điểm số cao nhất theo góc nhìn AI
    """
    # --- Kiểm tra bảng băm (Transposition Table Lookup) ---
    # TODO: Thêm logic kiểm tra TT ở đây nếu có
    # hash_entry = search_data.transposition_table.probe(...)
    # if hash_entry and hash_entry.depth >= depth_:
    #     if hash_entry.flag == EXACT: return hash_entry.score
    #     if hash_entry.flag == LOWER_BOUND: alpha = max(alpha, hash_entry.score)
    #     elif hash_entry.flag == UPPER_BOUND: beta = min(beta, hash_entry.score)
    #     if alpha >= beta: return hash_entry.score # Cutoff từ TT

    # --- Điều kiện dừng ---
    if depth_ == 0 or board_.is_game_over():
        return evaluate_position(board_, color=color) # Sử dụng hàm đánh giá của bạn

    # --- Lấy nước đi và SẮP XẾP ---
    legal_moves = list(board_.legal_moves)

    # Lấy thông tin để sắp xếp (ví dụ: từ TT, Killers, History)
    hash_move = None # TODO: Lấy từ TT probe nếu có (hash_entry.move)
    killers = search_data.get_killer_moves(ply)
    history = search_data.history_heuristic_table
    pv_move = None # TODO: Lấy từ TT hoặc lần lặp ID trước nếu có

    ordered_legal_moves = order_moves(
        board=board_,
        moves=legal_moves,
        pv_move=pv_move,        # Truyền thông tin nếu có
        hash_move=hash_move,    # Truyền thông tin nếu có
        killer_moves=killers,   # Truyền killers lấy được
        history=history,        # Truyền bảng history
        ply=ply                 # Truyền ply hiện tại
    )
    # -----------------------------

    max_score = float('-inf')
    best_move_found_in_node = None # Lưu nước đi tốt nhất tại nút này (cho TT)

    # --- Duyệt qua các nước đi ĐÃ SẮP XẾP ---
    for move in ordered_legal_moves:
        board_.push(move)
        # Gọi đệ quy Negamax, tăng ply lên 1
        score = -negamax(board_, depth_ - 1, -beta, -alpha, -color, ply + 1)
        board_.pop()

        if score >= max_score:
            max_score = score
            best_move_found_in_node = move # Cập nhật nước đi tốt nhất tại nút

        # --- Cắt tỉa Alpha-Beta ---
        alpha = max(alpha, score)
        if alpha >= beta:
            # *** CUTOFF ***
            # Nếu nước đi này gây cắt tỉa và là nước yên lặng (không bắt quân, không phong cấp)
            # thì có thể lưu nó làm Killer Move và cập nhật History Heuristic.
            if not board_.is_capture(move) and move.promotion is None:
                search_data.store_killer_move(ply, move)
                search_data.update_history_score(move, depth_) # Dùng depth_ còn lại làm trọng số
            break # Dừng duyệt các nước còn lại

    # --- Lưu vào bảng băm (Transposition Table Store) ---
    # TODO: Thêm logic lưu kết quả vào TT ở đây
    # flag = EXACT if max_score > initial_alpha else UPPER_BOUND # (Cần initial_alpha)
    # flag = LOWER_BOUND if max_score >= beta else flag
    # search_data.transposition_table.store(..., depth_, max_score, flag, best_move_found_in_node)

    return max_score


def get_best_move(board_: chess.Board, depth_: int) -> Optional[chess.Move]:
    """
    Tìm nước đi tốt nhất theo negamax, sử dụng sắp xếp nước đi ở gốc.
    :param board_: bàn cờ
    :param depth_: độ sâu tìm kiếm tối đa
    :return: nước đi tốt nhất (chess.Move) hoặc None nếu không có nước đi hợp lệ
    """
    global search_data # Sử dụng search_data toàn cục hoặc truyền vào
    search_data = DummySearchData() # Reset hoặc khởi tạo lại cho mỗi lần tìm kiếm mới (tùy chiến lược)

    best_move: Optional[chess.Move] = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    color = 1 if board_.turn == chess.WHITE else -1
    ply = 0 # Bắt đầu ở gốc, ply = 0

    # --- Lấy và SẮP XẾP nước đi ở gốc ---
    legal_moves = list(board_.legal_moves)
    if not legal_moves:
        return None # Không có nước đi nào

    # Ở gốc (ply=0), killers thường không áp dụng, history có thể có từ lần tìm kiếm trước
    hash_move = None # TODO: Probe TT ở gốc
    history = search_data.history_heuristic_table # Có thể dùng history cũ
    pv_move = None # TODO: Lấy từ lần lặp ID trước nếu có

    ordered_legal_moves = order_moves(
        board=board_,
        moves=legal_moves,
        pv_move=pv_move,
        hash_move=hash_move,
        killer_moves=None, # Không có killer cho ply 0
        history=history,
        ply=ply
    )
    # ------------------------------------

    # --- Duyệt qua các nước đi gốc ĐÃ SẮP XẾP ---
    for move in ordered_legal_moves:
        board_.push(move)
        # Bắt đầu tìm kiếm từ độ sâu depth_-1, và ply=1
        score = -negamax(board_, depth_ - 1, -beta, -alpha, -color, ply + 1)
        board_.pop()

        print(f"Move: {board_.san(move)}, Score: {score}") # In điểm từng nước đi gốc (debug)

        # Lưu nước đi tốt nhất tìm thấy cho đến nay
        if score >= best_score:
            best_score = score
            best_move = move

        # Alpha ở gốc cũng cập nhật, nhưng không dùng để cắt tỉa giữa các nước đi gốc
        # mà để làm cửa sổ cho các nhánh con.
        alpha = max(alpha, score)

        # (Không có cắt tỉa beta ở mức gốc này, vì chúng ta cần duyệt hết
        #  hoặc ít nhất là tìm được 1 nước đi tốt hơn alpha ban đầu)

    if best_move:
        san = board_.san(best_move)
        print(f"\nBest move found: {san}, Final Score: {best_score}")
    else:
        print("\nNo legal moves found or error.") # Xảy ra nếu legal_moves ban đầu rỗng

    return best_move # Trả về đối tượng chess.Move
