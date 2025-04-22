from typing import Optional

from evaluation_Pawn import evaluate_pawn_features
from evaluation_Knight import evaluate_knight_features
from evaluation_Rook import evaluate_rooks
from evaluation_Queen import evaluate_queens
from evaluation_King import evaluate_king_features
from collections import defaultdict
from evaluation_Bishop import evaluate_bishop_specifics as evaluate_bishop_features

from config import *


def get_game_phase(board):
    """
    Tính toán giai đoạn của ván cờ
    :param board: bàn cờ
    :return: Giá trị từ 0 (endgame) đến 256 (opening/midgame)
    """

    current_phase = 0
    for piece_type in PIECE_PHASE:
        current_phase += len(board.pieces(piece_type, chess.WHITE)) * PIECE_PHASE[piece_type]
        current_phase += len(board.pieces(piece_type, chess.BLACK)) * PIECE_PHASE[piece_type]

    current_phase = min(TOTAL_PHASE, max(0, current_phase))

    normalized_phase = (current_phase * 256 + (TOTAL_PHASE // 2)) // TOTAL_PHASE

    return min(256, max(0, normalized_phase))


# HAM TONG
def evaluate_position(board_):
    """
    Tổng hợp điểm tính toán từ các hàm đánh giá con theo góc nhìn quân trắng
    :param board_: bàn cờ
    :return: Điểm của bàn cờ theo góc nhìn quân trắng
    """
    # --- Kiểm tra Mate/Stalemate ---
    if board_.is_checkmate():
        # Ai bị chiếu hết? Nếu là lượt Đen -> Trắng thắng
        return CHECKMATE_SCORE if board_.turn == chess.BLACK else -CHECKMATE_SCORE
    if board_.is_stalemate() or board_.is_insufficient_material() or board_.is_seventyfive_moves() or board_.is_fivefold_repetition():
        return 0  # Hòa

    # --- Tính Game Phase ---
    phase = get_game_phase(board_)  # Giá trị từ 0 (EG) đến 256 (MG)

    # Lấy điểm MG/EG từ các hàm helper
    mg_material, eg_material = material(board_)
    mg_pst, eg_pst = piece_square_tables(board_)
    mg_king_safety, eg_king_safety = king_safety_tapered(board_)
    mg_passed_pawns, eg_passed_pawns = passed_pawns_tapered(board_)
    mg_rook_files, eg_rook_files = rook_files_tapered(board_)

    # Nội suy cho từng thành phần
    final_material = interpolate(mg_material, eg_material, phase)
    final_pst = interpolate(mg_pst, eg_pst, phase)
    final_king_safety = interpolate(mg_king_safety, eg_king_safety, phase)
    final_passed_pawns = interpolate(mg_passed_pawns, eg_passed_pawns, phase)
    final_rook_files = interpolate(mg_rook_files, eg_rook_files, phase)

    # Tính tổng đánh giá cuối cùng (áp dụng trọng số)
    total_eval = 0
    total_eval += final_material      * EVAL_WEIGHTS.get('material', 1.0) # Dùng .get để an toàn
    total_eval += final_pst           * EVAL_WEIGHTS.get('piece_square_tables', 0.0)
    total_eval += final_king_safety   * EVAL_WEIGHTS.get('king_safety', 0.0)
    total_eval += final_passed_pawns  * EVAL_WEIGHTS.get('passed_pawns', 0.0)
    total_eval += final_rook_files    * EVAL_WEIGHTS.get('rook_files', 0.0)

    # --- Trả về điểm cuối cùng (theo góc nhìn Trắng) ---
    # Hàm negamax sẽ tự xử lý perspective_multiplier
    return int(total_eval)  # Trả về số nguyên

# Mop-up evaluation

# material
def material(board: chess.Board) -> tuple[int, int]:
    """
    Hàm tính toán điểm material MG và EG theo góc nhìn quân trắng (Tối ưu hóa).
    :param board: bàn cờ chess.Board
    :return: Tuple (mg_value, eg_value)
    """
    mg_value = 0
    eg_value = 0
    # Lặp qua từng màu
    for color in [chess.WHITE, chess.BLACK]:
        # Xác định hệ số nhân (1 cho Trắng, -1 cho Đen)
        multiplier = 1 if color == chess.WHITE else -1
        # Lặp qua từng loại quân có giá trị trong bảng MG (bao gồm cả Tốt)
        for piece_type in PIECE_VALUES_MG:
            # Bỏ qua Vua vì giá trị material là 0
            if piece_type == chess.KING:
                continue
            # Lấy bitboard của các quân loại này
            squares = board.pieces(piece_type, color)
            # Đếm số lượng quân (rất nhanh từ bitboard)
            count = len(squares)
            # Cộng dồn điểm MG và EG
            mg_value += count * PIECE_VALUES_MG[piece_type] * multiplier
            eg_value += count * PIECE_VALUES_EG[piece_type] * multiplier
    return mg_value, eg_value


# --- Helper function để lấy bảng PST ---
def _get_pst_tables(piece_type: chess.PieceType) -> tuple[Optional[list], Optional[list]]:
    """ Lấy bảng điểm vị trí MG và EG cho loại quân. """
    if piece_type == chess.PAWN:
        return PAWN_POSITION_BONUS_MG, PAWN_POSITION_BONUS_EG
    elif piece_type == chess.KNIGHT:
        return KNIGHT_POSITION_BONUS_MG, KNIGHT_POSITION_BONUS_EG
    elif piece_type == chess.BISHOP:
        return BISHOP_POSITION_BONUS_MG, BISHOP_POSITION_BONUS_EG
    elif piece_type == chess.ROOK:
        return ROOK_POSITION_BONUS_MG, ROOK_POSITION_BONUS_EG
    elif piece_type == chess.QUEEN:
        return QUEEN_POSITION_BONUS_MG, QUEEN_POSITION_BONUS_EG
    elif piece_type == chess.KING:
        return KING_POSITION_BONUS_MG, KING_POSITION_BONUS_EG
    else:
        return None, None # Không có PST cho loại quân không xác định

# --- Hàm piece_square_tables (Đã tối ưu) ---
def piece_square_tables(board: chess.Board) -> tuple[int, int]:
    """
    Trả về (pst_mg, pst_eg) theo góc nhìn Trắng (Tối ưu hóa).
    """
    mg_eval = 0
    eg_eval = 0
    # Lặp qua các màu
    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        # Lặp qua tất cả các loại quân (bao gồm cả Vua)
        for piece_type in chess.PIECE_TYPES: # chess.PIECE_TYPES = [PAWN, KNIGHT, ..., KING]
            # Lấy bảng PST cho loại quân này
            pst_mg, pst_eg = _get_pst_tables(piece_type)

            # Nếu có bảng PST được định nghĩa
            if pst_mg is not None and pst_eg is not None:
                # Lấy bitboard chứa các ô của quân loại này, màu này
                squares_bitboard = board.pieces(piece_type, color)
                # Chỉ lặp qua các ô có quân đó
                for square in squares_bitboard:
                    # Tính index cho PST (xử lý lật bảng cho quân Đen)
                    pst_index = square if color == chess.WHITE else chess.square_mirror(square)
                    # Chuyển index 0-63 thành tọa độ hàng/cột 0-7
                    # Hàng 0 là rank 1, hàng 7 là rank 8
                    rank_idx = pst_index // 8
                    file_idx = pst_index % 8

                    # Lấy điểm bonus từ bảng (Lưu ý: PST thường định nghĩa từ rank 8 xuống 1)
                    # Nên index hàng cần là 7 - rank_idx
                    bonus_mg = pst_mg[7 - rank_idx][file_idx]
                    bonus_eg = pst_eg[7 - rank_idx][file_idx]

                    # Cộng dồn điểm
                    mg_eval += bonus_mg * multiplier
                    eg_eval += bonus_eg * multiplier

    return mg_eval, eg_eval


def interpolate(mg_score, eg_score, phase):
    """
    Nội suy điểm giữa MG và EG dựa trên phase.
    :param mg_score: Điểm MG
    :param eg_score: Điểm EG
    :param phase: giai đoạn của game [0, 256]
    :return: điểm nội suy
    """
    # Đảm bảo phase nằm trong khoảng [0, 256]
    phase = min(256, max(0, phase))
    # Công thức nội suy tuyến tính
    return ((mg_score * phase) + (eg_score * (256 - phase))) // 256


# --- Hàm King Safety Tapered (Tối ưu hóa) ---
KING_ZONE_MASKS = [0] * 64 # Precompute king zone masks if needed, or generate dynamically
for sq in chess.SQUARES:
    mask = 0
    rank = chess.square_rank(sq)
    file = chess.square_file(sq)
    for r_offset in [-1, 0, 1]:
        for f_offset in [-1, 0, 1]:
            # if r_offset == 0 and f_offset == 0: continue # Include king's square? Optional
            new_r, new_f = rank + r_offset, file + f_offset
            if 0 <= new_r <= 7 and 0 <= new_f <= 7:
                mask |= chess.BB_SQUARES[chess.square(new_f, new_r)]
    KING_ZONE_MASKS[sq] = mask

def _evaluate_king_safety_for_color(board: chess.Board, color: chess.Color) -> tuple[int, int]:
    """ Tính điểm an toàn MG và EG cho một màu vua (Tối ưu hóa). """
    mg_safety = 0
    eg_safety = 0
    king_square = board.king(color)
    if king_square is None: return -CHECKMATE_SCORE, -CHECKMATE_SCORE

    opponent = not color
    king_zone_mask = KING_ZONE_MASKS[king_square]

    # 1. Phạt bị tấn công gần Vua (Dùng bitboard)
    opponent_attacks = 0
    for piece_type in chess.PIECE_TYPES: # Lặp qua TẤT CẢ các loại quân địch
        if piece_type == chess.KING: continue # Thường không tính Vua địch tấn công vùng Vua mình
        for sq in board.pieces(piece_type, opponent):
            opponent_attacks |= board.attacks_mask(sq)

    attacked_king_zone_squares_count = bin(int(opponent_attacks & king_zone_mask)).count('1')

    mg_safety -= attacked_king_zone_squares_count * KING_ATTACKED_SQUARE_PENALTY_MG
    eg_safety -= attacked_king_zone_squares_count * KING_ATTACKED_SQUARE_PENALTY_EG

    # 2. Thưởng Tốt che chắn (chỉ MG) - Giữ nguyên logic đơn giản (khá nhanh)
    pawn_shield_bonus = 0
    king_rank = chess.square_rank(king_square)
    king_file = chess.square_file(king_square)
    shield_rank = king_rank + 1 if color == chess.WHITE else king_rank - 1
    if 0 <= shield_rank <= 7:
        friendly_pawns = board.pieces(chess.PAWN, color)
        for f_offset in [-1, 0, 1]:
            shield_f = king_file + f_offset
            if 0 <= shield_f <= 7:
                shield_sq_mask = chess.BB_SQUARES[chess.square(shield_f, shield_rank)]
                if bool(shield_sq_mask & int(friendly_pawns)): # Kiểm tra nhanh bằng bitboard
                    pawn_shield_bonus += PAWN_SHIELD_BONUS_MG
    mg_safety += pawn_shield_bonus
    # eg_safety += PAWN_SHIELD_BONUS_EG # = 0

    # 3. Bonus quyền nhập thành (chỉ MG)
    if board.has_castling_rights(color):
         mg_safety += CASTLING_RIGHTS_BONUS

    return mg_safety, eg_safety

def king_safety_tapered(board: chess.Board) -> tuple[int, int]:
    """ Tính chênh lệch điểm an toàn vua (Trắng - Đen) cho MG và EG """
    white_mg, white_eg = _evaluate_king_safety_for_color(board, chess.WHITE)
    black_mg, black_eg = _evaluate_king_safety_for_color(board, chess.BLACK)
    return white_mg - black_mg, white_eg - black_eg

# --- Precomputation for Pawn Attack Spans ---
WHITE_PAWN_FRONT_SPANS = [0] * 64
BLACK_PAWN_FRONT_SPANS = [0] * 64

def _compute_span(square, color):
    mask = 0
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    direction = 1 if color == chess.WHITE else -1
    files_to_check = range(max(0, file - 1), min(8, file + 2))
    current_rank = rank + direction
    while 0 <= current_rank <= 7:
        for check_file in files_to_check:
            mask |= chess.BB_SQUARES[chess.square(check_file, current_rank)]
        current_rank += direction
    return mask

def precompute_pawn_spans():
    print("Precomputing pawn attack spans...") # Debug print
    for sq in chess.SQUARES:
        WHITE_PAWN_FRONT_SPANS[sq] = _compute_span(sq, chess.WHITE)
        BLACK_PAWN_FRONT_SPANS[sq] = _compute_span(sq, chess.BLACK)
    print("Pawn attack spans precomputed.")

# Gọi hàm precomputation một lần khi module được import
precompute_pawn_spans()

def is_passed_optimized(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """ Kiểm tra Tốt thông bằng Bitboard (Hiệu quả hơn). """
    opponent = not color
    opponent_pawns_mask = board.pieces(chess.PAWN, opponent)
    # Tính hoặc lấy attack span mask đã tính trước
    attack_span_mask = WHITE_PAWN_FRONT_SPANS[square] if color == chess.WHITE else BLACK_PAWN_FRONT_SPANS[square]
    return not bool(opponent_pawns_mask & attack_span_mask)

def passed_pawns_tapered(board: chess.Board) -> tuple[int, int]:
    """ Tính điểm bonus Tốt thông cho MG và EG (Tối ưu hóa) """
    mg_bonus_total = 0
    eg_bonus_total = 0
    # Lặp qua màu
    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        pawns_bb = board.pieces(chess.PAWN, color)
        for sq in pawns_bb:
            # Dùng hàm is_passed đã tối ưu
            if is_passed_optimized(board, sq, color):
                rank = chess.square_rank(sq)
                mirrored_rank_index = rank if color == chess.WHITE else 7 - rank
                # Kiểm tra index hợp lệ trước khi truy cập
                if 0 <= mirrored_rank_index < len(PASSED_PAWN_BONUS_MG):
                    mg_bonus = PASSED_PAWN_BONUS_MG[mirrored_rank_index]
                    eg_bonus = PASSED_PAWN_BONUS_EG[mirrored_rank_index]
                    mg_bonus_total += mg_bonus * multiplier
                    eg_bonus_total += eg_bonus * multiplier
    return mg_bonus_total, eg_bonus_total

# --- Hàm Rooks on Files Tapered ---
def rook_files_tapered(board: chess.Board) -> tuple[int, int]:
    """ Tính điểm bonus cho Xe trên cột mở/bán mở (Tối ưu hóa) """
    mg_bonus_total = 0
    eg_bonus_total = 0
    pawns = board.pawns # Lấy bitboard tất cả Tốt một lần

    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        rooks_bb = board.pieces(chess.ROOK, color)
        friendly_pawns = board.pieces(chess.PAWN, color)
        seventh_rank_mask = chess.BB_RANK_7 if color == chess.WHITE else chess.BB_RANK_2

        for sq in rooks_bb:
            file = chess.square_file(sq)
            file_mask = chess.BB_FILES[file]

            pawns_on_file = bool(pawns & file_mask)
            friendly_pawns_on_file = bool(friendly_pawns & file_mask)

            is_open = not pawns_on_file
            is_semi_open = not friendly_pawns_on_file # Bán mở cho phe ta

            bonus_mg = 0
            bonus_eg = 0

            if is_open:
                bonus_mg += ROOK_OPEN_FILE_BONUS_MG
                bonus_eg += ROOK_OPEN_FILE_BONUS_EG
            elif is_semi_open:
                bonus_mg += ROOK_SEMI_OPEN_FILE_BONUS_MG
                bonus_eg += ROOK_SEMI_OPEN_FILE_BONUS_EG

            # Bonus nếu ở hàng 7/2
            if bool(chess.BB_SQUARES[sq] & seventh_rank_mask):
                bonus_mg += ROOK_ON_7TH_BONUS_MG
                bonus_eg += ROOK_ON_7TH_BONUS_EG

            mg_bonus_total += bonus_mg * multiplier
            eg_bonus_total += bonus_eg * multiplier

    return mg_bonus_total, eg_bonus_total




# --------- UNUSED -------------- #
# Evaluation of Pieces
def evaluate_pieces(board_: chess.Board) -> float:
    """
    Tổng hợp đánh giá các loại quân trên bàn cờ
    """
    evaluation = 0
    phase_ratio = get_game_phase(board_)

    evaluation += evaluate_pawn_features(board_)
    evaluation += evaluate_knight_features(board_)
    evaluation += evaluate_bishop_features(board_)
    evaluation += evaluate_rooks(board_, chess.WHITE)
    evaluation -= evaluate_rooks(board_, chess.BLACK)
    evaluation += evaluate_queens(board_, chess.WHITE)
    evaluation -= evaluate_queens(board_, chess.BLACK)
    evaluation += evaluate_king_features(board_, phase_ratio)

    return evaluation


# Evaluation Patterns

# Mobility
def mobility(board_):
    """
    Mobility nâng cao: tính số nước đi từng quân (không tính tốt), phân theo loại quân,
    nhân trọng số, rồi tính chênh lệch trắng - đen.
    """
    white_score = 0
    black_score = 0

    for move in board_.legal_moves:
        piece = board_.piece_at(move.from_square)
        if piece and piece.piece_type in MOBILITY_WEIGHTS:
            weight = MOBILITY_WEIGHTS[piece.piece_type]
            if piece.color == chess.WHITE:
                white_score += weight
            else:
                black_score += weight

    return white_score - black_score


# Center Control (Tạm thời chưa cho)


# Connectivity (Tạm thời chưa cho)


# Trapped Pieces
def trapped_pieces(board_):
    """
    Đánh giá các quân bị mắc kẹt (trapped pieces) theo góc nhìn trắng.
    Tối ưu: cache legal moves theo from_square để tránh lặp.
    """
    evaluation = 0

    # Cache legal moves theo từng ô xuất phát
    legal_by_square = defaultdict(list)
    for move in board_.legal_moves:
        legal_by_square[move.from_square].append(move)

    def is_trapped(piece, square, legal_moves):
        if piece.piece_type not in TRAPPED_PIECE_PENALTY:
            return False

        if len(legal_moves) <= 1:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            if file in [0, 7] or rank in [0, 7]:
                return True
        return False

    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece and piece.piece_type in TRAPPED_PIECE_PENALTY:
            legal_moves = legal_by_square.get(square, [])
            if is_trapped(piece, square, legal_moves):
                penalty = TRAPPED_PIECE_PENALTY[piece.piece_type]
                evaluation += -penalty if piece.color == chess.WHITE else penalty

    return evaluation


# Space
def space(board_):
    """
    Đánh giá không gian kiểm soát theo góc nhìn trắng.
    Tính số ô trống được kiểm soát trên phần sân đối phương.
    """
    white_space = 0
    black_space = 0
    central_squares = [chess.D4, chess.E4, chess.D5, chess.E5]

    for square in chess.SQUARES:
        # Bỏ qua ô đang có quân
        if board_.piece_at(square):
            continue

        white_attackers = board_.attackers(chess.WHITE, square)
        black_attackers = board_.attackers(chess.BLACK, square)

        rank = chess.square_rank(square)

        # White kiểm soát ô trên nửa sân của đen
        if white_attackers and rank >= 4:
            white_space += 1
            if square in central_squares:
                white_space += 0.5

        # Black kiểm soát ô trên nửa sân của trắng
        if black_attackers and rank <= 3:
            black_space += 1
            if square in central_squares:
                black_space += 0.5

    return SPACE_WEIGHT * (white_space - black_space)


# manhattan_distance
def manhattan_distance(square1, square2):
    """
    Tính khoảng cách manhattan giữa hai ô
    :param square1: ô thứ nhất
    :param square2: ô thứ hai
    :return: khoảng cách manhattan
    """
    file1, rank1 = chess.square_file(square1), chess.square_rank(square1)
    file2, rank2 = chess.square_file(square2), chess.square_rank(square2)
    return abs(file1 - file2) + abs(rank1 - rank2)

# Mop-up evaluation
