import chess
from typing import List, Optional, Tuple, Dict
import config

# from evaluation import static_exchange_evaluation # Cần import hàm SEE trong evaluation

PIECE_VALUES = config.PIECE_VALUES


def get_piece_value(piece_type: Optional[chess.PieceType]) -> int:
    return PIECE_VALUES.get(piece_type, 0) if piece_type else 0


def is_open_or_semi_open(board: chess.Board, file: int, color: chess.Color) -> bool:
    """Kiểm tra cột có mở hoặc bán mở (không có tốt phe mình)."""
    for rank in range(8):
        square = chess.square(file, rank)
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN and piece.color == color:
            return False  # Có tốt phe mình -> không phải mở/bán mở
    return True  # Không có tốt phe mình


def get_least_valuable_attacker(board: chess.Board, attackers_mask: chess.Bitboard, side_to_move: chess.Color) -> \
Optional[chess.Square]:
    """
    Tìm ô của quân tấn công có giá trị thấp nhất trong tập attackers_mask.
    Trả về None nếu không tìm thấy.
    """
    min_value = float('inf')
    lva_square = None

    # Duyệt qua các loại quân từ thấp đến cao (Tốt -> Hậu)
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        # Tìm các quân loại này của phe side_to_move trong tập attackers_mask
        pieces_of_type: chess.Bitboard = board.pieces(piece_type, side_to_move) & attackers_mask
        # Kiểm tra xem Bitboard có rỗng không
        if pieces_of_type:  # Cách kiểm tra Bitboard rỗng trong python-chess
            # Chọn ô có bit cao nhất (hoặc thấp nhất)
            # *** SỬA Ở ĐÂY: Chuyển Bitboard thành int trước khi gọi msb/lsb ***
            try:
                # Ưu tiên dùng phương thức tích hợp sẵn của Bitboard nếu có (ít gây lỗi hơn)
                # Tùy phiên bản python-chess, tên phương thức có thể khác nhau chút ít
                # hoặc không tồn tại. Thử .msb() hoặc .lsb()
                lva_square = pieces_of_type.msb()  # Thử .msb() trước
            except AttributeError:
                try:
                    # Nếu .msb() không có, thử ép kiểu int rồi dùng chess.msb
                    lva_square = chess.msb(int(pieces_of_type))
                except Exception as e:
                    # Xử lý lỗi nếu cả hai cách đều không hoạt động (nên log lỗi)
                    print(f"Error finding msb/lsb for pieces_of_type: {pieces_of_type}, Error: {e}")
                    return None  # Hoặc xử lý khác

            # Nếu lva_square đã được tìm thấy thành công
            if lva_square is not None:
                min_value = get_piece_value(piece_type)
                return lva_square  # Trả về ngay khi tìm thấy loại quân nhỏ nhất

    return None  # Không tìm thấy quân tấn công nào hợp lệ trong mask


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

    # Các mức điểm cơ bản để phân cấp
    HASH_MOVE_SCORE = 100_000_000
    PV_MOVE_SCORE = 99_000_000
    WINNING_CAPTURE_BASE = 80_000_000  # SEE sẽ cộng vào đây
    PROMOTION_QUEEN_SCORE = 75_000_000
    KILLER_1_SCORE = 70_000_000
    KILLER_2_SCORE = 69_000_000
    PROMOTION_OTHER_BASE = 65_000_000  # Giá trị quân phong sẽ cộng vào
    QUIET_MOVE_BASE = 0  # Điểm history và bonus sẽ cộng vào đây
    LOSING_CAPTURE_BASE = -80_000_000  # SEE (âm) sẽ cộng vào đây

    # Phạm vi điểm cho SEE và Heuristic yên lặng để tránh chồng lấn quá nhiều
    MAX_SEE_SCORE_RANGE = 10_000_000  # Ví dụ: -5M -> +5M
    MAX_QUIET_BONUS_RANGE = 5_000_000  # Ví dụ: history + bonus khác

    # Tính điểm cho từng nước đi
    for move in moves:
        score = 0
        is_capture = board.is_capture(move)
        is_promotion = move.promotion is not None

        # --- Ưu tiên 1: Hash / PV Move ---
        if move == hash_move:
            score = HASH_MOVE_SCORE
        elif move == pv_move:
            score = PV_MOVE_SCORE
        else:
            # --- Ưu tiên 2 & 7: Bắt quân (Đánh giá bằng SEE) ---
            if is_capture:
                see_score = static_exchange_evaluation(board, move)

                # Xử lý en passant nếu SEE không xử lý (ví dụ trả về 0)
                if see_score == 0 and board.is_en_passant(move):
                    see_score = get_piece_value(chess.PAWN)

                # Giới hạn điểm SEE để không ảnh hưởng quá lớn đến các bậc ưu tiên
                capped_see = max(min(see_score, MAX_SEE_SCORE_RANGE // 2), -MAX_SEE_SCORE_RANGE // 2)

                if see_score >= 0:  # Bắt quân tốt / hòa vốn
                    score = WINNING_CAPTURE_BASE + capped_see
                else:  # Bắt quân lỗ
                    score = LOSING_CAPTURE_BASE + capped_see  # capped_see là số âm

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

                # Tính các bonus từ hàm của bạn
                piece = board.piece_at(move.from_square)
                if piece:
                    # Bonus chiếu (nếu có)
                    try:  # board.gives_check có thể chậm, cân nhắc
                        if board.gives_check(move):
                            quiet_score += 400  # Giá trị ví dụ
                    except AssertionError:  # Có thể xảy ra nếu nước đi không hợp lệ (ít khả năng nếu list đầu vào là legal_moves)
                        pass

                    # Bonus nhập thành
                    if board.is_castling(move):
                        quiet_score += 300  # Giá trị ví dụ

                    # Bonus Xe cột mở/bán mở
                    if piece.piece_type == chess.ROOK:
                        to_file = chess.square_file(move.to_square)
                        if is_open_or_semi_open(board, to_file, piece.color):
                            quiet_score += 200  # Giá trị ví dụ

                    # Bonus Tốt tiến gần phong cấp
                    elif piece.piece_type == chess.PAWN:
                        rank = chess.square_rank(move.to_square)
                        color = board.turn
                        if color == chess.WHITE and rank >= 5:  # Rank 6, 7, 8 (1-based index theo chess lib)
                            quiet_score += (rank - 4) * 50  # Ví dụ
                        elif color == chess.BLACK and rank <= 2:  # Rank 3, 2, 1
                            quiet_score += (3 - rank) * 50  # Ví dụ

                # Giới hạn tổng điểm yên lặng
                score = min(quiet_score, MAX_QUIET_BONUS_RANGE)

        move_scores[move] = score

    # Sắp xếp danh sách moves dựa trên điểm số đã tính toán (từ cao đến thấp)
    ordered_moves = sorted(moves, key=lambda m: move_scores.get(m, -float('inf')), reverse=True)

    return ordered_moves
