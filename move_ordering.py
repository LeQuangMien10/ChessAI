import chess
from typing import List, Optional, Tuple, Dict
import config

# from evaluation import static_exchange_evaluation # Cần import hàm SEE trong evaluation

PIECE_VALUES = config.PIECE_VALUES


def get_piece_value(piece_type: Optional[chess.PieceType]) -> int:
    return PIECE_VALUES.get(piece_type, 0) if piece_type else 0


def is_open_or_semi_open(board: chess.Board, file: int, color: chess.Color) -> bool:
    """Kiểm tra cột có mở hoặc bán mở (không có tốt phe mình)."""
    pawns = board.pawns
    file_mask = chess.BB_FILES[file]
    friendly_pawns = board.pieces(chess.PAWN, color)
    friendly_on_file = bool(friendly_pawns & file_mask)
    return not friendly_on_file # True nếu không có Tốt mình


def get_least_valuable_attacker(board: chess.Board, attackers_mask: chess.Bitboard, side_to_move: chess.Color) -> Optional[chess.Square]:
    """Tìm ô của quân tấn công có giá trị thấp nhất."""
    attackers_mask_int = int(attackers_mask) # Chuyển mask đầu vào thành int một lần

    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        # Lấy bitboard của quân, cũng chuyển thành int
        pieces_of_type_bb = board.pieces(piece_type, side_to_move)
        pieces_of_type_int = int(pieces_of_type_bb)

        # Thực hiện phép AND trên hai số nguyên
        pieces_on_attack_squares_int = pieces_of_type_int & attackers_mask_int

        # Kiểm tra kết quả (là số nguyên)
        if pieces_on_attack_squares_int != 0:
            try:
                # chess.lsb hoạt động tốt với số nguyên
                lva_square_index = chess.lsb(pieces_on_attack_squares_int)
                return lva_square_index # Trả về int (chess.Square)
            except Exception as e:
                 # Vẫn nên giữ lại để bắt lỗi không mong muốn
                 print(f"ERROR: chess.lsb failed on non-zero int {pieces_on_attack_squares_int}: {e}")
                 return None
    return None

def static_exchange_evaluation(board: chess.Board, move: chess.Move) -> int:
    """
    Tính giá trị trao đổi tĩnh (SEE) cho nước đi `move` trên bàn cờ `board`.
    Chỉ có ý nghĩa nếu `move` là một nước đi bắt quân.
    Sử dụng phương pháp lặp để mô phỏng chuỗi bắt quân.
    """
    target_square = move.to_square
    source_square = move.from_square

    # Lấy quân bị bắt ban đầu
    captured_piece_type = None
    if board.is_en_passant(move):
        captured_piece_type = chess.PAWN
    else:
        captured_piece = board.piece_at(target_square)
        if captured_piece:
            captured_piece_type = captured_piece.piece_type
        else:
            return 0  # Nước đi không bắt quân

    # Lấy quân tấn công ban đầu
    attacker_piece = board.piece_at(source_square)
    if not attacker_piece:
        # Trường hợp lạ, có thể do lỗi gọi hàm với nước đi không hợp lệ
        print(f"Warning: No piece found at source square {chess.square_name(source_square)} for move {move.uci()}")
        return 0

    # Danh sách lưu giá trị quân cờ tại ô đích ở mỗi bước trao đổi
    # gain[0] = 0 (giá trị ảo trước khi có quân nào)
    # gain[1] = giá trị quân bị bắt đầu tiên
    # gain[2] = giá trị quân tấn công đầu tiên (bị bắt lại)
    # gain[3] = giá trị quân phòng thủ đầu tiên (bị bắt lại)
    # ...
    gain = [0] * 32  # Khởi tạo mảng đủ lớn
    gain[0] = get_piece_value(captured_piece_type)

    current_attacker_value = get_piece_value(attacker_piece.piece_type)
    side_to_move = not board.turn  # Bên phòng thủ sẽ ăn lại đầu tiên

    # --- Mô phỏng bàn cờ ---
    # Sử dụng bitboard để theo dõi các quân cờ đang chiếm chỗ
    # Ban đầu bao gồm tất cả các quân trừ quân tấn công ban đầu (vì nó đã di chuyển)
    occupied = board.occupied & ~chess.BB_SQUARES[source_square]
    # Bỏ qua quân bị bắt nếu không phải en passant (quân tấn công chiếm ô đó)
    if not board.is_en_passant(move):
        occupied &= ~chess.BB_SQUARES[target_square]

    # --- Vòng lặp mô phỏng trao đổi ---
    depth = 1  # Bắt đầu với quân tấn công đầu tiên đã ở ô đích
    while True:
        # Tìm tất cả các quân đang tấn công ô đích, *từ trạng thái hiện tại*
        all_attackers_defenders = board.attackers_mask(side_to_move, target_square) & occupied

        if not all_attackers_defenders:
            break  # Không còn ai ăn được nữa

        # Tìm quân có giá trị thấp nhất trong số đó
        lva_square = get_least_valuable_attacker(board, all_attackers_defenders, side_to_move)

        if lva_square is None:
            break  # Không tìm thấy quân tấn công hợp lệ (lạ?)

        # Lưu giá trị của quân vừa bị bắt (quân tấn công trước đó)
        gain[depth] = current_attacker_value
        depth += 1

        # Cập nhật quân tấn công hiện tại (là quân LVA vừa tìm được)
        lva_piece = board.piece_at(lva_square)
        if not lva_piece: break  # Lỗi không mong muốn
        current_attacker_value = get_piece_value(lva_piece.piece_type)

        # Xóa quân LVA khỏi bàn cờ mô phỏng
        occupied &= ~chess.BB_SQUARES[lva_square]

        # Đổi lượt
        side_to_move = not side_to_move

        # Giới hạn độ sâu để tránh lỗi (hiếm khi cần)
        if depth >= 32:
            break

    # --- Tính điểm SEE từ danh sách gain ---
    # Áp dụng công thức negamax ngược từ cuối danh sách
    score = 0
    for i in range(depth - 1, 0, -1):
        score = max(0, gain[i] - score)  # Bên phòng thủ chỉ ăn lại nếu có lợi hoặc hòa vốn

    # Nước đi đầu tiên là của bên ta, nên ta muốn tối đa hóa (gain[0] - score_cua_doi_phuong)
    final_score = gain[0] - score

    return final_score


# --- Hàm sắp xếp chính ---
MVV_LVA_MULTIPLIER = 100 # Hệ số nhân cho giá trị quân bị bắt

def order_moves(
        board: chess.Board,
        moves: List[chess.Move],
        pv_move: Optional[chess.Move] = None,
        hash_move: Optional[chess.Move] = None,
        killer_moves: Optional[Tuple[Optional[chess.Move], Optional[chess.Move]]] = None,
        history: Optional[Dict[Tuple[chess.Square, chess.Square], int]] = None,
        ply: int = 0  # Độ sâu hiện tại (có thể dùng cho history)
) -> List[chess.Move]:
    """
    Sắp xếp nước đi, tích hợp SEE và các heuristic vị trí/chiến thuật.

    Thứ tự ưu tiên:
    1. Hash Move / PV Move
    2. Bắt quân tốt/hòa vốn (SEE >= 0), sắp xếp theo SEE giảm dần.
    3. Phong Hậu (không bắt quân)
    4. Killer Moves
    5. Phong quân khác (không bắt quân), sắp xếp theo giá trị quân phong.
    6. Nước đi yên lặng (Quiet Moves):
        - Điểm History Heuristic
        - Bonus cho Chiếu
        - Bonus cho Nhập thành
        - Bonus cho Xe vào cột mở/bán mở
        - Bonus cho Tốt tiến gần phong cấp
        -> Sắp xếp theo tổng điểm này.
    7. Nước đi bắt quân bất lợi (SEE < 0), sắp xếp theo SEE tăng dần (ít tệ nhất lên trước).
    """
    move_scores: Dict[chess.Move, int] = {}

    # Các mức điểm cơ bản
    HASH_MOVE_SCORE = 200_000_000 # Tăng base score để MVV-LVA không vượt qua
    PV_MOVE_SCORE = 190_000_000
    # --- MVV-LVA sẽ xác định điểm cho bắt quân ---
    # Base cho bắt quân sẽ thấp hơn, điểm MVV-LVA sẽ quyết định thứ tự
    WINNING_CAPTURE_MVV_LVA_BASE = 100_000_000 # Base cho các nước bắt quân có MVV-LVA > 0
    EQUAL_CAPTURE_MVV_LVA_BASE = 90_000_000   # Base cho các nước hòa vốn MVV-LVA (ví dụ PxP)
    # --- Điểm SEE sẽ dùng để hạ cấp các nước bắt quân tệ ---
    LOSING_CAPTURE_SEE_THRESHOLD = -50 # Ngưỡng SEE để coi là bắt quân tệ
    LOSING_CAPTURE_SCORE_PENALTY = 50_000_000 # Phạt nặng nếu SEE âm

    PROMOTION_QUEEN_SCORE= 150_000_000
    KILLER_1_SCORE       = 80_000_000
    KILLER_2_SCORE       = 79_000_000
    PROMOTION_OTHER_BASE = 140_000_000
    QUIET_MOVE_BASE      = 0
    # Losing captures (không có SEE check) sẽ có điểm rất thấp tự nhiên do MVV-LVA âm

    MAX_QUIET_BONUS_RANGE = 5_000_000

    # Tính điểm cho từng nước đi
    for move in moves:
        score = 0
        is_capture = board.is_capture(move) or board.is_en_passant(move)
        is_promotion = move.promotion is not None

        # --- Ưu tiên 1: Hash / PV Move ---
        if move == hash_move:
            score = HASH_MOVE_SCORE
        elif move == pv_move:
            score = PV_MOVE_SCORE
        else:
            # --- Ưu tiên 2 & 7: Bắt quân (Đánh giá bằng SEE) ---
            if is_capture:
                captured_piece_type = None
                if board.is_en_passant(move): captured_piece_type = chess.PAWN
                else:
                    captured_piece = board.piece_at(move.to_square)
                    if captured_piece: captured_piece_type = captured_piece.piece_type

                attacker_piece_type = board.piece_type_at(move.from_square)

                if captured_piece_type and attacker_piece_type:
                    victim_value = get_piece_value(captured_piece_type)
                    attacker_value = get_piece_value(attacker_piece_type)
                    mvv_lva_score = (victim_value * MVV_LVA_MULTIPLIER) - attacker_value

                    # Gán điểm dựa trên MVV-LVA
                    if mvv_lva_score >= 0:
                        score = WINNING_CAPTURE_MVV_LVA_BASE + mvv_lva_score
                    else: # MVV-LVA âm (ví dụ: QxB) -> điểm sẽ thấp hơn base
                        score = WINNING_CAPTURE_MVV_LVA_BASE + mvv_lva_score # Vẫn dùng base này

                    # --- Optional: Kiểm tra SEE để hạ cấp nước bắt quân tệ ---
                    see_score = static_exchange_evaluation(board, move)
                    if see_score < LOSING_CAPTURE_SEE_THRESHOLD:
                        # Phạt nặng nếu SEE cho thấy lỗ nặng
                        # Giữ nguyên thứ tự tương đối MVV-LVA nhưng giảm tổng điểm
                        score -= LOSING_CAPTURE_SCORE_PENALTY
                        # Hoặc có thể đặt một base riêng cho losing SEE captures
                        # score = LOSING_CAPTURE_BASE + mvv_lva_score # Dùng base khác

                else: # Không lấy được type -> lỗi hoặc nước đi lạ
                    score = -float('inf') # Đẩy xuống cuối

            # --- Ưu tiên 3 & 5: Phong cấp (Không bắt quân) ---
            elif is_promotion:
                if move.promotion == chess.QUEEN:
                    score = PROMOTION_QUEEN_SCORE
                else:
                    promo_value = get_piece_value(move.promotion)
                    score = PROMOTION_OTHER_BASE + promo_value

            # --- Ưu tiên 4: Killer Moves (Không phải bắt quân/phong cấp/hash/pv) ---
            elif killer_moves:
                if move == killer_moves[0]:
                    score = KILLER_1_SCORE
                elif move == killer_moves[1]:
                    score = KILLER_2_SCORE

            # --- Ưu tiên 6: Nước đi yên lặng (Không phải các loại trên) ---
            if score == 0:  # Chỉ tính điểm yên lặng nếu chưa được gán điểm cao hơn
                quiet_score = QUIET_MOVE_BASE
                # Lấy điểm History
                if history:
                    history_val = history.get((move.from_square, move.to_square), 0)
                    # Giới hạn điểm history
                    quiet_score += min(history_val, MAX_QUIET_BONUS_RANGE // 2)
                # Giới hạn tổng điểm yên lặng
                score = min(quiet_score, MAX_QUIET_BONUS_RANGE)

        move_scores[move] = score

    # Sắp xếp danh sách moves dựa trên điểm số đã tính toán (từ cao đến thấp)
    ordered_moves = sorted(moves, key=lambda m: move_scores.get(m, -float('inf')), reverse=True)

    return ordered_moves
