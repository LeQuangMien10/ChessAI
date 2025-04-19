import time

import chess.polyglot
from typing import Optional  # Thêm Optional để gợi ý kiểu cho best_move

# Import các thành phần cần thiết từ các file khác
from config import *  # Giả sử config chứa PIECE_VALUES nếu orders.py không định nghĩa lại
from evaluation import evaluate_position
from move_ordering import order_moves, static_exchange_evaluation  # <<<--- IMPORT HÀM SẮP XẾP
from transposition_table import TranspositionTable, NodeType


NMP_MIN_DEPTH = 3
NMP_REDUCTION = 3
LMR_MIN_DEPTH = 3
LMR_MIN_MOVE_COUNT = 4

CHECKMATE_SCORE = 3000000
CHECKMATE_THRESHOLD = 2900000


MAX_PLY = 64

# --- Cấu trúc dữ liệu tạm thời (nếu chưa có) ---
# Nếu bạn chưa có cấu trúc quản lý search data (TT, Killers, History),
# bạn có thể dùng placeholder trước. Khi có, bạn sẽ truyền nó vào.
class DummySearchData:
    """Placeholder nếu chưa có cấu trúc dữ liệu search thực sự."""

    def __init__(self):
        # self.transposition_table = None  # Thay bằng TT thật sau
        self.killer_moves = {}  # Ví dụ: dict dạng {ply: [move1, move2]}
        self.history_heuristic_table = {}  # Ví dụ: dict dạng {(from, to): score}

    def get_killer_moves(self, ply):
        # Trả về cặp killer moves cho ply hiện tại (có thể là None)
        return self.killer_moves.get(ply, (None, None))

    def store_killer_move(self, ply, move):
        # Logic lưu trữ killer move (ví dụ: đẩy move mới vào, bỏ move cũ)
        if ply not in self.killer_moves:
            self.killer_moves[ply] = [None, None]
        if move != self.killer_moves[ply][0]:  # Tránh trùng lặp
            self.killer_moves[ply][1] = self.killer_moves[ply][0]
            self.killer_moves[ply][0] = move

    def update_history_score(self, move, depth):
        # Logic cập nhật điểm history (ví dụ: tăng điểm cho nước đi gây cắt tỉa)
        key = (move.from_square, move.to_square)
        self.history_heuristic_table[key] = self.history_heuristic_table.get(key, 0) + depth * depth


# Khởi tạo đối tượng search data (tạm thời)
search_data = DummySearchData()


# ----------------------------------------------------

def quiescence_search(board_, alpha, beta, tt):
    """
    Tìm kiếm yên tĩnh xét các nước bắt quân, phong cấp
    :param board_: bàn cờ
    :param alpha: alpha
    :param beta: beta
    :param tt: Bảng băm
    :return: Điểm sau khi đánh giá
    """

    zobrist_key = chess.polyglot.zobrist_hash(board_)
    tt_probe_result = tt.probe(zobrist_key, 0, alpha, beta)

    if tt_probe_result is not None:
        tt_score, _ = tt_probe_result
        if tt_score is not None:
            return tt_score

    # --- Stand-pat score ---
    eval_score = evaluate_position(board_)
    perspective_multiplier = 1 if board_.turn == chess.WHITE else -1
    stand_pat = eval_score * perspective_multiplier

    # --- Beta cutoff check (stand-pat) ---
    if stand_pat >= beta:
        return beta

    # --- Update alpha ---
    alpha = max(alpha, stand_pat)


    # --- Generate and Order Tactical Moves ---
    # Chỉ xét bắt quân (có thể thêm phong cấp nếu muốn)
    tactical_moves = [move for move in board_.legal_moves if board_.is_capture(move)]
    # TODO: Sắp xếp tactical_moves (ví dụ: dùng SEE hoặc MVV-LVA)
    # Ví dụ đơn giản: dùng SEE
    move_scores = {move: static_exchange_evaluation(board_, move) for move in tactical_moves}
    ordered_tactical_moves = sorted(tactical_moves, key=lambda m: move_scores.get(m, -float('inf')), reverse=True)

    # --- Loop through tactical moves ---
    for move in ordered_tactical_moves:
        # --- Delta Pruning (tùy chọn nâng cao) ---
        # if stand_pat + get_piece_value(board_.piece_type_at(move.to_square)) + DELTA_MARGIN < alpha:
        #     continue # Nếu bắt quân cũng không đủ để nâng alpha, bỏ qua

        board_.push(move)
        score = -quiescence_search(board_, -beta, -alpha, tt)
        board_.pop()

        # --- Update alpha/beta ---
        if score >= beta:
            tt.store(zobrist_key, 0, beta, NodeType.LOWER_BOUND, move)
            return beta # Fail high

        alpha = max(alpha, score)

    return alpha

def negamax(board_: chess.Board, depth_: int, alpha: float, beta: float, ply: int,
            tt: TranspositionTable, search_data_: DummySearchData, do_null: bool = True):  # <<< Thêm tham số ply
    """
    Negamax với cắt tỉa Alpha-Beta và sắp xếp nước đi.
    :param board_: bàn cờ
    :param depth_: độ sâu còn lại
    :param alpha: alpha
    :param beta: beta
    :param ply: Độ sâu hiện tại từ gốc (dùng cho killers/history)
    :param tt: bảng TT
    :param search_data_: search data
    :param do_null: cờ để tránh NMP liên tiếp
    :return: điểm số cao nhất theo góc nhìn AI
    """

    # --- 1. Kiểm tra Kết thúc Game & Độ sâu ---
    if board_.is_checkmate():
        return -CHECKMATE_SCORE + ply
    if board_.is_stalemate() or board_.is_insufficient_material() or board_.is_seventyfive_moves() or board_.is_fivefold_repetition():
        return 0 # Hòa

    # --- Giảm độ sâu ---
    is_root = (ply == 0)
    if depth_ <= 0:
        # Gọi Quiescence Search thay vì evaluate_position trực tiếp
        return quiescence_search(board_, alpha, beta, tt)

    # --- 2. Thăm dò bảng băm ---
    original_alpha = alpha
    zobrist_key = chess.polyglot.zobrist_hash(board_)
    tt_probe_result = tt.probe(zobrist_key, depth_, alpha, beta)
    tt_move: Optional[chess.Move] = None
    tt_score: Optional[int] = None

    if tt_probe_result is not None:
        tt_score, tt_move_maybe = tt_probe_result
        if tt_score is not None and not is_root:
            return tt_score
        if tt_move_maybe:
            tt_move = tt_move_maybe

    # --- 3. Null Move Pruning (NMP) ---
    non_pawn_king_material = sum(
        len(board_.pieces(pt, chess.WHITE)) + len(board_.pieces(pt, chess.BLACK))
        for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
    )
    can_nmp = (
            do_null and
            depth_ >= NMP_MIN_DEPTH and
            not is_root and
            not board_.is_check() and
            non_pawn_king_material > 4  # Hoặc một ngưỡng khác bạn chọn (ví dụ > 4)
    )

    if can_nmp:
        board_.push(chess.Move.null())

        # Tìm kiếm với độ sâu giảm và cửa sổ zero (-beta, -beta+1)
        null_move_score = -negamax(board_, depth_ - 1 - NMP_REDUCTION, -beta, -beta + 1, ply + 1, tt, search_data_,
                                   do_null=False)  # Đặt do_null=False
        board_.pop()  # Hoàn tác nước đi rỗng

        # Nếu nước đi rỗng gây cắt tỉa beta, trả về beta
        is_mate_score = abs(null_move_score) > CHECKMATE_THRESHOLD
        if null_move_score >= beta and not is_mate_score:
            return beta  # Hoặc null_move_score

    # --- 4. Sinh và Sắp xếp Nước đi ---
    legal_moves = list(board_.legal_moves)
    if not legal_moves: # Có thể xảy ra nếu NMP dẫn đến thế bí (rất hiếm nếu logic đúng)
        return 0 # Hòa

    # Lấy thông tin sắp xếp
    killers = search_data_.get_killer_moves(ply)
    history = search_data_.history_heuristic_table
    # Ưu tiên tt_move (hash_move) nếu có
    pv_move = None # Lấy từ ID hoặc TT nếu có chiến lược lưu PV

    ordered_legal_moves = order_moves(
        board=board_,
        moves=legal_moves,
        pv_move=pv_move,
        hash_move=tt_move, # Sử dụng TT_MOVE từ PROBE
        killer_moves=killers,
        history=history,
        ply=ply
    )

    # --- 5. Vòng lặp Negamax ---
    max_score = float('-inf')
    best_move_found_in_node: Optional[chess.Move] = None
    move_count = 0

    for move in ordered_legal_moves:
        move_count += 1
        is_capture = board_.is_capture(move)
        is_promotion = move.promotion is not None
        # gives_check = board_.gives_check(move) # Có thể tốn kém, cân nhắc
        is_quiet = not is_capture and not is_promotion #and not gives_check

        board_.push(move)

        score: int = 0
        # --- Late Move Reduction (LMR) ---
        reduction = 0
        can_lmr = (
            depth_ >= LMR_MIN_DEPTH and
            move_count > LMR_MIN_MOVE_COUNT and
            is_quiet and
            move != tt_move and # Không giảm hash move
            (killers is None or move not in killers) # Không giảm killer moves
        )

        if can_lmr:
            # Tính toán mức giảm (ví dụ đơn giản)
            # reduction = LMR_BASE_REDUCTION + (depth_ // 4) + (move_count // 8) # Công thức ví dụ
            reduction = 1 # Giảm 1 đơn giản
            reduction = min(reduction, depth_ - 2) # Đảm bảo depth còn lại ít nhất 1
            reduction = max(reduction, 0)

            # Tìm kiếm giảm với Zero Window
            score = -negamax(board_, depth_ - 1 - reduction, -alpha - 1, -alpha,
                             ply + 1, tt, search_data_, do_null=True)
        else:
            # Đặt reduction = -1 để đánh dấu là chưa tìm kiếm hoặc tìm kiếm đủ sâu
            reduction = -1 # Hoặc 0 nếu không dùng logic re-search phức tạp

        # --- Re-search nếu LMR có vẻ tốt hoặc tìm kiếm bình thường ---
        # Nếu tìm kiếm giảm tốt hơn alpha (hoặc nếu không dùng LMR)
        if reduction != -1 and score > alpha: # Điều kiện re-search sau LMR
            score = -negamax(board_, depth_ - 1, -alpha - 1, -alpha,
                             ply + 1, tt, search_data_, do_null=True) # Có thể thử ZW trước re-search full window
            if score > alpha: # Vẫn tốt -> Re-search full window
                 score = -negamax(board_, depth_ - 1, -beta, -alpha,
                                  ply + 1, tt, search_data_, do_null=True)

        elif reduction == -1 : # Tìm kiếm bình thường (không LMR)
             score = -negamax(board_, depth_ - 1, -beta, -alpha,
                              ply + 1, tt, search_data_, do_null=True)

        board_.pop()

        # --- Cập nhật điểm tốt nhất ---
        if score > max_score:
            max_score = score
            best_move_found_in_node = move

        # --- Cắt tỉa Alpha-Beta ---
        alpha = max(alpha, score)
        if alpha >= beta:
            # *** CUTOFF (Fail High / Beta Cutoff) ***
            if is_quiet: # Chỉ cập nhật killer/history cho nước yên lặng
                search_data_.store_killer_move(ply, move)
                search_data_.update_history_score(move, depth_)
            break # Dừng duyệt

    # --- 6. TT Store ---
    node_type: int
    if max_score <= original_alpha:
        node_type = NodeType.UPPER_BOUND # Fail Low
    elif max_score >= beta:
        node_type = NodeType.LOWER_BOUND # Fail High
    else:
        node_type = NodeType.EXACT      # PV Node

    # Chỉ lưu nếu không bị cắt tỉa ở gốc hoặc có nước đi tốt
    if best_move_found_in_node is not None or node_type == NodeType.LOWER_BOUND: # Cần có nước đi để lưu LOWER_BOUND
        tt.store(zobrist_key, depth_, max_score, node_type, best_move_found_in_node)

    return max_score


def get_best_move(board_: chess.Board, depth_: int, tt: TranspositionTable) -> Optional[chess.Move]:
    """
    Tìm nước đi tốt nhất theo negamax, sử dụng sắp xếp nước đi ở gốc, bảng băm (nên dùng thêm ID).
    :param board_: bàn cờ
    :param depth_: độ sâu tìm kiếm tối đa
    :param tt: Bảng băm (Transition Table)
    :return: nước đi tốt nhất (chess.Move) hoặc None nếu không có nước đi hợp lệ
    """
    start_time = time.time()

    global search_data  # Sử dụng search_data toàn cục hoặc truyền vào
    search_data = DummySearchData()  # Reset hoặc khởi tạo lại cho mỗi lần tìm kiếm mới (tùy chiến lược)

    best_move: Optional[chess.Move] = None
    best_score_this_iteration = float('-inf') # Đổi tên để rõ ràng hơn khi có ID
    alpha = float('-inf')
    beta = float('inf')
    ply = 0  # Bắt đầu ở gốc, ply = 0

    # --- Iterative Deepening (KHUYẾN KHÍCH MẠNH MẼ) ---
    # Nên thực hiện tìm kiếm trong vòng lặp for current_depth in range(1, depth_ + 1):
    # Để đơn giản, vẫn giữ tìm kiếm 1 lần như trước
    current_depth = depth_ # Thay thế depth_ bằng current_depth trong vòng lặp ID

    # --- Lấy và Sắp xếp Nước đi ở Gốc ---
    legal_moves = list(board_.legal_moves)
    if not legal_moves: return None

    zobrist_key = chess.polyglot.zobrist_hash(board_)
    hash_move = tt.get_pv_move(zobrist_key) # Lấy từ lần lặp ID trước
    history = search_data.history_heuristic_table
    pv_move = hash_move

    ordered_legal_moves = order_moves(
        board=board_, moves=legal_moves, pv_move=pv_move,
        hash_move=hash_move, killer_moves=None, history=history, ply=ply
    )

    # --- Duyệt qua các nước đi gốc ---
    for i, move in enumerate(ordered_legal_moves):
        board_.push(move)
        # Gọi negamax với độ sâu hiện tại - 1
        score = -negamax(board_, current_depth - 1, -beta, -alpha, ply + 1, tt, search_data,
                         do_null=True)
        board_.pop()

        # Trong Iterative Deepening, bạn sẽ cập nhật alpha ở đây
        # và có thể có cửa sổ tìm kiếm hẹp hơn cho các nước đi sau nước đi đầu tiên.
        # Ví dụ: if i == 0: alpha = score ... else: score = -negamax(..., -alpha-1, -alpha,...)

        print(f"Move: {board_.san(move)}, Score: {score:.0f}") # In điểm

        if score > best_score_this_iteration:
            best_score_this_iteration = score
            best_move = move
            # Trong ID, bạn sẽ cập nhật alpha = score ở đây cho nước đi đầu tiên

        # Cập nhật alpha (quan trọng cho các lần gọi sau ở gốc)
        alpha = max(alpha, score)

        # Có thể thêm logic dừng sớm trong ID nếu cần

    # In thông tin (ví dụ: PV từ TT)
    pv_line = []
    curr_board = board_.copy()
    key = zobrist_key
    try:
        for _ in range(current_depth): # Giới hạn độ dài PV theo độ sâu
            entry = tt.table.get(key)
            if not entry or not entry.best_move: break
            move = entry.best_move
            if move not in curr_board.legal_moves: break # An toàn
            san = curr_board.san(move)
            pv_line.append(san)
            curr_board.push(move)
            key = chess.polyglot.zobrist_hash(curr_board)
    except Exception as e:
        print(f"Error extracting PV: {e}") # Bắt lỗi

    if best_move:
        san = board_.san(best_move)
        pv_str = " ".join(pv_line)
        print(f"\nDepth: {current_depth}, Best: {san}, Score: {best_score_this_iteration:.0f}, PV: {pv_str}, Time: {time.time() - start_time:.2f}s, TT: {len(tt)}")
    else:
        print("\nNo legal moves found or error.")

    return best_move