import time

import chess.polyglot
from typing import Optional  # Thêm Optional để gợi ý kiểu cho best_move

# Import các thành phần cần thiết từ các file khác
from config import *  # Giả sử config chứa PIECE_VALUES nếu orders.py không định nghĩa lại
from evaluation import evaluate_position
from move_ordering import order_moves, static_exchange_evaluation, get_piece_value  # <<<--- IMPORT HÀM SẮP XẾP
from transposition_table import TranspositionTable, NodeType

NMP_MIN_DEPTH = 3
NMP_REDUCTION = 3
LMR_MIN_DEPTH = 3
LMR_MIN_MOVE_COUNT = 4

QSEARCH_SEE_PRUNING_THRESHOLD = -75

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

    # zobrist_key = chess.polyglot.zobrist_hash(board_)
    # tt_probe_result = tt.probe(zobrist_key, 0, alpha, beta)
    #
    # if tt_probe_result is not None:
    #     tt_score, _ = tt_probe_result
    #     if tt_score is not None:
    #         return tt_score

    # --- Stand-pat score ---
    eval_score = evaluate_position(board_)
    perspective_multiplier = 1 if board_.turn == chess.WHITE else -1
    stand_pat = eval_score * perspective_multiplier

    # --- Beta cutoff check (stand-pat) ---
    if stand_pat >= beta:
        return beta

    # --- Update alpha ---
    alpha = max(alpha, stand_pat)

    # --- Generate and Order Tactical Moves (Captures + Promotions) ---
    tactical_moves_with_scores = []
    for move in board_.legal_moves:
        is_capture = board_.is_capture(move)
        is_promotion = move.promotion is not None

        if is_capture:
            see_score = static_exchange_evaluation(board_, move)
            # --- SEE Pruning ---
            if see_score >= QSEARCH_SEE_PRUNING_THRESHOLD:
                 # Ưu tiên dựa trên SEE (hoặc MVV-LVA)
                 # Gán điểm cao cho bắt quân tốt để xét trước
                 # Có thể dùng SEE trực tiếp hoặc cộng vào base lớn
                 capture_priority = 10000 + see_score # Ví dụ base
                 tactical_moves_with_scores.append((move, capture_priority))
            # else: Bỏ qua nước bắt quân có SEE quá thấp

        elif is_promotion:
            # Ưu tiên phong cấp (đặc biệt là Hậu)
            promo_value = get_piece_value(move.promotion)
            promotion_priority = 8000 + promo_value # Base thấp hơn capture tốt
            tactical_moves_with_scores.append((move, promotion_priority))

    # Sắp xếp các nước đi chiến thuật theo điểm ưu tiên (cao xuống thấp)
    ordered_tactical_moves = sorted(tactical_moves_with_scores, key=lambda item: item[1], reverse=True)

    # --- Loop through tactical moves ---
    # best_move_q = None # Lưu nước đi tốt nhất trong QSearch (cho TT)
    for move, _ in ordered_tactical_moves: # Chỉ cần move từ tuple
        board_.push(move)
        score = -quiescence_search(board_, -beta, -alpha, tt)
        board_.pop()

        # --- Update alpha/beta ---
        if score > alpha: # Tìm được điểm tốt hơn alpha
             alpha = score
             # best_move_q = move # Cập nhật nước đi tốt nhất
             if alpha >= beta:
                  # --- Beta Cutoff ---
                  # Lưu vào TT (depth=0, loại LOWER_BOUND)
                  # zobrist_key = chess.polyglot.zobrist_hash(board_) # Tính lại key nếu chưa có
                  # tt.store(zobrist_key, 0, beta, NodeType.LOWER_BOUND, best_move_q) # Lưu beta và nước đi gây cắt tỉa
                  return beta # Fail high

    # --- Lưu vào TT nếu alpha được cải thiện (optional) ---
    # if alpha > stand_pat: # Chỉ lưu nếu tìm được nước tốt hơn stand-pat
    #     node_type = NodeType.EXACT # Vì nó nằm trong khoảng [stand_pat, beta)
    #     zobrist_key = chess.polyglot.zobrist_hash(board_)
    #     tt.store(zobrist_key, 0, alpha, node_type, best_move_q)

    return alpha # Trả về alpha cuối cùng (điểm tốt nhất tìm được)


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
        return 0  # Hòa

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
    if not legal_moves:  # Có thể xảy ra nếu NMP dẫn đến thế bí (rất hiếm nếu logic đúng)
        return 0  # Hòa

    # Lấy thông tin sắp xếp
    killers = search_data_.get_killer_moves(ply)
    history = search_data_.history_heuristic_table
    # Ưu tiên tt_move (hash_move) nếu có
    pv_move = None  # Lấy từ ID hoặc TT nếu có chiến lược lưu PV

    ordered_legal_moves = order_moves(
        board=board_,
        moves=legal_moves,
        pv_move=pv_move,
        hash_move=tt_move,  # Sử dụng TT_MOVE từ PROBE
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
        is_quiet = not is_capture and not is_promotion  # and not gives_check

        board_.push(move)

        score: int = 0
        # --- Late Move Reduction (LMR) ---
        reduction = 0
        can_lmr = (
                depth_ >= LMR_MIN_DEPTH and
                move_count > LMR_MIN_MOVE_COUNT and
                is_quiet and
                move != tt_move and  # Không giảm hash move
                (killers is None or move not in killers)  # Không giảm killer moves
        )

        if can_lmr:
            # Tính toán mức giảm (ví dụ đơn giản)
            # reduction = LMR_BASE_REDUCTION + (depth_ // 4) + (move_count // 8) # Công thức ví dụ
            reduction = 1  # Giảm 1 đơn giản
            reduction = min(reduction, depth_ - 2)  # Đảm bảo depth còn lại ít nhất 1
            reduction = max(reduction, 0)

            # Tìm kiếm giảm với Zero Window
            score = -negamax(board_, depth_ - 1 - reduction, -alpha - 1, -alpha,
                             ply + 1, tt, search_data_, do_null=True)
        else:
            # Đặt reduction = -1 để đánh dấu là chưa tìm kiếm hoặc tìm kiếm đủ sâu
            reduction = -1  # Hoặc 0 nếu không dùng logic re-search phức tạp

        # --- Re-search nếu LMR có vẻ tốt hoặc tìm kiếm bình thường ---
        # Nếu tìm kiếm giảm tốt hơn alpha (hoặc nếu không dùng LMR)
        if reduction != -1 and score > alpha:  # Điều kiện re-search sau LMR
            score = -negamax(board_, depth_ - 1, -alpha - 1, -alpha,
                             ply + 1, tt, search_data_, do_null=True)  # Có thể thử ZW trước re-search full window
            if score > alpha:  # Vẫn tốt -> Re-search full window
                score = -negamax(board_, depth_ - 1, -beta, -alpha,
                                 ply + 1, tt, search_data_, do_null=True)

        elif reduction == -1:  # Tìm kiếm bình thường (không LMR)
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
            if is_quiet:  # Chỉ cập nhật killer/history cho nước yên lặng
                search_data_.store_killer_move(ply, move)
                search_data_.update_history_score(move, depth_)
            break  # Dừng duyệt

    # --- 6. TT Store ---
    node_type: int
    if max_score <= original_alpha:
        node_type = NodeType.UPPER_BOUND  # Fail Low
    elif max_score >= beta:
        node_type = NodeType.LOWER_BOUND  # Fail High
    else:
        node_type = NodeType.EXACT  # PV Node

    # Chỉ lưu nếu không bị cắt tỉa ở gốc hoặc có nước đi tốt
    if best_move_found_in_node is not None or node_type == NodeType.LOWER_BOUND:  # Cần có nước đi để lưu LOWER_BOUND
        tt.store(zobrist_key, depth_, max_score, node_type, best_move_found_in_node)

    return max_score


def get_best_move(board_: chess.Board, target_depth: int, tt: TranspositionTable, time_limit_seconds: Optional[float] = TIME_LIMIT) -> Optional[chess.Move]:
    """
    Tìm nước đi tốt nhất theo negamax, sử dụng sắp xếp nước đi ở gốc,
    bảng băm và ID.
    :param board_: bàn cờ
    :param target_depth: độ sâu tìm kiếm tối đa
    :param tt: Bảng băm (Transition Table)
    :param time_limit_seconds: Thời gian giới hạn
    :return: nước đi tốt nhất (chess.Move) hoặc None nếu không có nước đi hợp lệ
    """
    start_time = time.time()

    global search_data  # Sử dụng search_data toàn cục hoặc truyền vào
    search_data = DummySearchData()  # Reset hoặc khởi tạo lại cho mỗi lần tìm kiếm mới (tùy chiến lược)

    # --- Biến cho Iterative Deepening ---
    best_move_completed_depth: Optional[chess.Move] = None
    best_score_completed_depth = float('-inf')
    pv_line_completed_depth = [] # Lưu PV từ lần lặp sâu nhất
    final_depth_completed = 0

    # Lấy danh sách nước đi hợp lệ một lần ở đầu
    legal_moves = list(board_.legal_moves)
    if not legal_moves:
        print("\nError: No legal moves at root.")
        return None # Trả về None nếu không có nước đi

    # --- Vòng lặp Iterative Deepening ---
    for current_depth in range(1, target_depth + 1):
        ply = 0
        alpha = -CHECKMATE_SCORE # Đặt lại alpha/beta cho mỗi độ sâu
        beta = CHECKMATE_SCORE
        # --- Biến tạm cho độ sâu HIỆN TẠI ---
        best_move_this_iteration: Optional[chess.Move] = None
        best_score_this_iteration = float('-inf') # Điểm tốt nhất ở độ sâu hiện tại
        search_interrupted = False

        # --- Lấy và Sắp xếp Nước đi ở Gốc (quan trọng là dùng kết quả từ lần lặp trước) ---
        zobrist_key = chess.polyglot.zobrist_hash(board_)
        # Ưu tiên nước đi từ TT của lần lặp trước (nếu có)
        hash_move = tt.get_pv_move(zobrist_key) # Hoặc lấy từ pv_line_completed_depth[0] nếu có
        history = search_data.history_heuristic_table # History có thể tích lũy

        ordered_legal_moves = order_moves(
            board=board_, moves=legal_moves,
            pv_move=hash_move, # Sử dụng nước đi tốt nhất từ lần trước
            hash_move=hash_move, # Có thể giống pv_move ở gốc
            killer_moves=None, history=history, ply=ply
        )

        # Nếu chỉ có 1 nước đi, không cần tìm sâu hơn nữa
        if len(ordered_legal_moves) == 1 and current_depth > 1:
             best_move_completed_depth = ordered_legal_moves[0]
             final_depth_completed = current_depth - 1
             print(f"\nForced move: {board_.san(best_move_completed_depth)}")
             # Có thể tính điểm cho nước đi này nếu muốn, nhưng không cần thiết
             break # Thoát vòng lặp ID

        print(f"\n--- Searching Depth {current_depth} ---")

        # --- Duyệt qua các nước đi gốc ở độ sâu hiện tại ---
        for i, move in enumerate(ordered_legal_moves):

            # KIỂM TRA THỜI GIAN NGAY TỪ ĐẦU VÒNG LẶP
            if time_limit_seconds is not None:
                elapsed_time = time.time() - start_time
                if elapsed_time > time_limit_seconds * 0.7:
                    print(f"\nTime limit ({elapsed_time:.1f}s) reached BEFORE starting move {i+1} at depth {current_depth}. Returning best from depth {final_depth_completed}.")
                    search_interrupted = True # Đặt cờ ngắt
                    break # Thoát khỏi vòng lặp for move

            # <<<--- Tính SAN trước khi push/pop ---<<<
            try:
                move_san = board_.san(move)
            except ValueError: # Xử lý nếu move không hợp lệ (ít khả năng nhưng đề phòng)
                 move_san = move.uci()
                 print(f"Warning: Could not get SAN for move {move.uci()} in current position. Using UCI.")


            board_.push(move)
            score = float('-inf')

            # --- Logic Aspiration Windows (Cải thiện) ---
            # use_aspiration = current_depth > 2 # Chỉ dùng từ depth 3 trở lên
            use_aspiration = False # Turn off for now
            if use_aspiration and i == 0 and best_score_completed_depth > -CHECKMATE_THRESHOLD : # Chỉ dùng khi có điểm số hợp lệ từ lần trước
                window_margin = 100 # Biên độ thử nghiệm
                # Đặt cửa sổ quanh điểm số tốt nhất của lần lặp TRƯỚC ĐÓ
                search_alpha = max(-CHECKMATE_SCORE + 1, best_score_completed_depth - window_margin)
                search_beta = min(CHECKMATE_SCORE - 1, best_score_completed_depth + window_margin)
                # print(f"  Trying aspiration window [{search_alpha}, {search_beta}] for {move_san}") # Debug

                score = -negamax(board_, current_depth - 1, -search_beta, -search_alpha,
                                 ply + 1, tt, search_data, do_null=True)

                # --- Re-search nếu Aspiration thất bại ---
                if score <= search_alpha: # Fail low
                    print(f"    Aspiration fail low ({score:.0f} <= {search_alpha}). Re-searching below alpha...")
                    # Tìm kiếm lại với cửa sổ (-inf, alpha cũ)
                    score = -negamax(board_, current_depth - 1, -beta, -search_alpha, # <<<--- Dùng -beta và -search_alpha
                                     ply + 1, tt, search_data, do_null=True)
                elif score >= search_beta: # Fail high
                    print(f"    Aspiration fail high ({score:.0f} >= {search_beta}). Re-searching above beta...")
                     # Tìm kiếm lại với cửa sổ (beta cũ, +inf)
                    score = -negamax(board_, current_depth - 1, -search_beta, -alpha, # <<<--- Dùng -search_beta và -alpha
                                     ply + 1, tt, search_data, do_null=True)

            else: # Không dùng Aspiration hoặc lần lặp đầu
                 # Tìm kiếm với cửa sổ đầy đủ
                 score = -negamax(board_, current_depth - 1, -beta, -alpha,
                                  ply + 1, tt, search_data, do_null=True)

            board_.pop()


            # --- KIỂM TRA THỜI GIAN SAU KHI SEARCH XONG 1 NƯỚC ---
            # Quan trọng: Kiểm tra lại sau mỗi lệnh gọi negamax tốn thời gian
            if time_limit_seconds is not None:
                 current_elapsed = time.time() - start_time
                 if current_elapsed > time_limit_seconds:
                      print(f"\nTime limit ({current_elapsed:.1f}s) reached AFTER searching move {move_san} at depth {current_depth}. Returning best from depth {final_depth_completed}.")
                      search_interrupted = True # Đặt cờ ngắt
                      # Không cập nhật best_move_this_iteration nữa vì search chưa hoàn tất
                      break # Thoát khỏi vòng lặp for move


            # print(f"  Move: {move_san}, Score: {score:.0f}") # In điểm từng nước

            # --- Cập nhật nước đi tốt nhất cho lần lặp này ---
            if score > best_score_this_iteration:
                best_score_this_iteration = score
                best_move_this_iteration = move

            # --- Cập nhật Alpha (Quan trọng cho các nước tiếp theo ở gốc) ---
            # Nước đi đầu tiên đặt cận dưới alpha
            if score > alpha:
                alpha = score

        # --- Kết thúc vòng lặp duyệt nước đi gốc ---

        # --- CHỈ CẬP NHẬT KẾT QUẢ HOÀN THÀNH NẾU KHÔNG BỊ NGẮT ---
        if not search_interrupted:
            # Nếu vòng lặp for kết thúc bình thường (không break do time limit)
            if best_move_this_iteration is not None:
                best_move_completed_depth = best_move_this_iteration
                best_score_completed_depth = best_score_this_iteration
                final_depth_completed = current_depth  # Cập nhật độ sâu hoàn thành

                # --- Trích xuất PV và In thông tin ---
                pv_line_current = []
                curr_board_pv = board_.copy()
                key_pv = zobrist_key
                try:
                    for _ in range(current_depth):
                        entry = tt.table.get(key_pv)
                        if not entry or not entry.best_move: break  # Dừng nếu không có entry hoặc best_move
                        # Không lọc theo node_type ở đây, lấy nước đi tốt nhất TT gợi ý
                        pv_move_in_line = entry.best_move
                        # Kiểm tra nước đi có hợp lệ không TRƯỚC khi push
                        if pv_move_in_line not in curr_board_pv.legal_moves:
                            # print(f"PV extraction error: {pv_move_in_line.uci()} not legal in {curr_board_pv.fen()}")
                            break
                        san = curr_board_pv.san(pv_move_in_line)
                        pv_line_current.append(san)
                        curr_board_pv.push(pv_move_in_line)
                        key_pv = chess.polyglot.zobrist_hash(curr_board_pv)
                        if len(pv_line_current) > MAX_PLY: break
                    pv_line_completed_depth = pv_line_current
                    pv_str = " ".join(pv_line_completed_depth)
                    best_move_san_print = board_.san(best_move_completed_depth)
                    print(
                        f"Depth {current_depth} completed. Best: {best_move_san_print}, Score: {best_score_completed_depth:.0f}, PV: {pv_str}")
                except Exception as e:
                    print(f"Error extracting PV or SAN at depth {current_depth}: {e}")
                    pv_line_completed_depth = []

            else:
                # Lỗi: Hoàn thành depth nhưng không tìm thấy nước đi nào?
                print(
                    f"CRITICAL Warning: Completed depth {current_depth} but no best move found this iteration. Search may be flawed.")
                # Không cập nhật kết quả hoàn thành, giữ nguyên từ lần trước
                break  # Dừng ID

            # Kiểm tra Mate Score sau khi hoàn thành depth
            if abs(best_score_completed_depth) > CHECKMATE_THRESHOLD:
                print(
                    f"Mate score ({best_score_completed_depth:.0f}) found at depth {current_depth}. Stopping search.")
                break  # Dừng ID
        else:
            # Nếu bị ngắt giữa chừng (search_interrupted == True)
            # Không cập nhật kết quả hoàn thành, thoát vòng lặp ID
            break

    # --- Kết thúc vòng lặp Iterative Deepening ---

    final_elapsed_time = time.time() - start_time

    # Trả về kết quả từ độ sâu hoàn thành cuối cùng
    if best_move_completed_depth:
        try:
            san = board_.san(best_move_completed_depth)
        except:
            san = best_move_completed_depth.uci()
        pv_str = " ".join(pv_line_completed_depth)  # PV từ độ sâu hoàn thành cuối cùng
        print(f"\n--- Search Finished ---")
        print(
            f"Final Depth Completed: {final_depth_completed}, Best Move: {san}, Score: {best_score_completed_depth:.0f}")
        print(f"Principal Variation: {pv_str}")
        print(f"Time: {final_elapsed_time:.2f}s, TT Entries: {len(tt)}")
    else:
        # Chỉ xảy ra nếu không có nước đi hợp lệ ban đầu hoặc lỗi rất lạ
        print("\nCritical Error: No best move found after search.")
        if legal_moves: return legal_moves[0]  # Fallback

    return best_move_completed_depth