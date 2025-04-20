from evaluation_Pawn import evaluate_pawn_features
from evaluation_Knight import evaluate_knight_features
from evaluation_Rook import evaluate_rooks
from evaluation_Queen import evaluate_queens
from evaluation_King import evaluate_king_features
from collections import defaultdict
from evaluation_Bishop import evaluate_bishop_specifics as evaluate_bishop_features

import chess
from time import perf_counter

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
    Hàm tính toán điểm midgame và endgame theo góc nhìn quân trắng
    :param board: bàn cờ
    :return: Tuples (mg_value, eg_value)
    """
    mg_value = 0
    eg_value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            mg_val = PIECE_VALUES_MG[piece.piece_type]
            eg_val = PIECE_VALUES_EG[piece.piece_type]
            if piece.color == chess.WHITE:
                mg_value += mg_val
                eg_value += eg_val
            else:
                mg_value -= mg_val
                eg_value -= eg_val
    return mg_value, eg_value


# piece_square_tables
def piece_square_tables(board: chess.Board) -> tuple[int, int]:
    """ Trả về (pst_mg, pst_eg) theo góc nhìn Trắng. """
    mg_eval = 0
    eg_eval = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # Lấy đúng bảng PST cho MG và EG
            pst_mg = None
            pst_eg = None
            piece_type = piece.piece_type

            if piece_type == chess.PAWN:
                pst_mg, pst_eg = PAWN_POSITION_BONUS_MG, PAWN_POSITION_BONUS_EG
            elif piece_type == chess.KNIGHT:
                pst_mg, pst_eg = KNIGHT_POSITION_BONUS_MG, KNIGHT_POSITION_BONUS_EG
            elif piece_type == chess.BISHOP:
                pst_mg, pst_eg = BISHOP_POSITION_BONUS_MG, BISHOP_POSITION_BONUS_EG
            elif piece_type == chess.ROOK:
                pst_mg, pst_eg = ROOK_POSITION_BONUS_MG, ROOK_POSITION_BONUS_EG
            elif piece_type == chess.QUEEN:
                pst_mg, pst_eg = QUEEN_POSITION_BONUS_MG, QUEEN_POSITION_BONUS_EG
            elif piece_type == chess.KING:
                pst_mg, pst_eg = KING_POSITION_BONUS_MG, KING_POSITION_BONUS_EG

            if pst_mg is not None and pst_eg is not None:
                # Tính index dựa trên màu quân
                index = square if piece.color == chess.WHITE else chess.square_mirror(square)
                row, col = divmod(index, 8)  # Hoặc dùng 7 - index // 8, index % 8 như cũ
                row_idx = 7 - row  # Vì bảng thường định nghĩa từ rank 8 xuống 1

                bonus_mg = pst_mg[row_idx][col]
                bonus_eg = pst_eg[row_idx][col]

                if piece.color == chess.WHITE:
                    mg_eval += bonus_mg
                    eg_eval += bonus_eg
                else:
                    mg_eval -= bonus_mg
                    eg_eval -= bonus_eg

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


# --- Hàm King Safety Tapered ---
def _get_surrounding_squares(square):
    """ Lấy các ô xung quanh (vua) """
    surrounding = []
    rank = chess.square_rank(square)
    file = chess.square_file(square)
    for r_offset in [-1, 0, 1]:
        for f_offset in [-1, 0, 1]:
            if r_offset == 0 and f_offset == 0: continue
            new_r, new_f = rank + r_offset, file + f_offset
            if 0 <= new_r <= 7 and 0 <= new_f <= 7:
                surrounding.append(chess.square(new_f, new_r))
    return surrounding

def _evaluate_king_safety_for_color(board: chess.Board, color: chess.Color) -> tuple[int, int]:
    """ Tính điểm an toàn MG và EG cho một màu vua """
    mg_safety = 0
    eg_safety = 0
    king_square = board.king(color)
    if king_square is None:
        return (-CHECKMATE_SCORE, -CHECKMATE_SCORE) # Vua đã bị bắt? (rất tệ)

    opponent = not color
    surrounding_squares = _get_surrounding_squares(king_square)

    # 1. Phạt bị tấn công gần Vua
    attack_penalty_mg = 0
    attack_penalty_eg = 0
    for sq in surrounding_squares:
        attackers = board.attackers(opponent, sq)
        if attackers:
            attack_penalty_mg += len(attackers) * KING_ATTACKED_SQUARE_PENALTY_MG
            attack_penalty_eg += len(attackers) * KING_ATTACKED_SQUARE_PENALTY_EG
    mg_safety -= attack_penalty_mg
    eg_safety -= attack_penalty_eg

    # 2. Thưởng Tốt che chắn (chỉ MG)
    pawn_shield_bonus = 0
    king_rank = chess.square_rank(king_square)
    king_file = chess.square_file(king_square)
    # Chỉ xét các ô ngay phía trước Vua (thường là quan trọng nhất)
    shield_ranks = [king_rank + 1] if color == chess.WHITE else [king_rank - 1]
    if 0 <= shield_ranks[0] <= 7:
        for f_offset in [-1, 0, 1]:
            shield_f = king_file + f_offset
            if 0 <= shield_f <= 7:
                shield_sq = chess.square(shield_f, shield_ranks[0])
                piece = board.piece_at(shield_sq)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    pawn_shield_bonus += PAWN_SHIELD_BONUS_MG
    mg_safety += pawn_shield_bonus
    # eg_safety += PAWN_SHIELD_BONUS_EG # Thường là 0

    # 3. Bonus quyền nhập thành (chỉ MG)
    if board.has_castling_rights(color):
         # Kiểm tra xem đã nhập thành chưa, nếu chưa mới cộng bonus quyền
          mg_safety += CASTLING_RIGHTS_BONUS
              # Hoặc có thể cộng bonus lớn hơn nếu ĐÃ nhập thành? Tùy logic

    # King PST đã được tính trong piece_square_tables, không cần tính lại ở đây

    return mg_safety, eg_safety

def king_safety_tapered(board: chess.Board) -> tuple[int, int]:
    """ Tính chênh lệch điểm an toàn vua (Trắng - Đen) cho MG và EG """
    white_mg, white_eg = _evaluate_king_safety_for_color(board, chess.WHITE)
    black_mg, black_eg = _evaluate_king_safety_for_color(board, chess.BLACK)
    return (white_mg - black_mg, white_eg - black_eg)

# --- Hàm Passed Pawns Tapered ---
def is_passed(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """ Kiểm tra xem Tốt ở ô square có phải là Tốt thông không """
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    opponent = not color
    direction = 1 if color == chess.WHITE else -1

    # Kiểm tra các cột trước mặt (cột hiện tại và 2 cột liền kề)
    for check_file in range(max(0, file - 1), min(8, file + 2)):
        # Kiểm tra các ô từ hàng tiếp theo đến hàng cuối
        current_rank = rank + direction
        while 0 <= current_rank <= 7:
            check_square = chess.square(check_file, current_rank)
            piece = board.piece_at(check_square)
            if piece and piece.piece_type == chess.PAWN and piece.color == opponent:
                return False # Có Tốt đối phương chặn
            current_rank += direction
    return True # Không có Tốt đối phương chặn

def passed_pawns_tapered(board: chess.Board) -> tuple[int, int]:
    """ Tính điểm bonus Tốt thông cho MG và EG (góc nhìn Trắng) """
    mg_bonus_total = 0
    eg_bonus_total = 0
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    for sq in white_pawns:
        if is_passed(board, sq, chess.WHITE):
            rank = chess.square_rank(sq) # rank 0-7
            mg_bonus = PASSED_PAWN_BONUS_MG[rank]
            eg_bonus = PASSED_PAWN_BONUS_EG[rank]
            mg_bonus_total += mg_bonus
            eg_bonus_total += eg_bonus
            # Optional: Thêm bonus nếu được Vua bảo vệ/gần Vua ở EG

    for sq in black_pawns:
        if is_passed(board, sq, chess.BLACK):
            rank = chess.square_rank(sq)
            # Lấy bonus từ bảng nhưng đảo ngược index rank cho Đen
            # Rank 0 của đen là index 7, rank 1 là index 6,... rank 7 là index 0
            mirrored_rank_index = 7 - rank
            mg_bonus = PASSED_PAWN_BONUS_MG[mirrored_rank_index]
            eg_bonus = PASSED_PAWN_BONUS_EG[mirrored_rank_index]
            mg_bonus_total -= mg_bonus # Trừ điểm của Đen
            eg_bonus_total -= eg_bonus
            # Optional: Thêm bonus nếu được Vua bảo vệ/gần Vua ở EG

    return mg_bonus_total, eg_bonus_total

# --- Hàm Rooks on Files Tapered ---
def _is_file_open(board: chess.Board, file: int) -> bool:
    """ Kiểm tra cột có hoàn toàn không có Tốt nào không """
    for rank in range(8):
        piece = board.piece_at(chess.square(file, rank))
        if piece and piece.piece_type == chess.PAWN:
            return False
    return True

def _is_file_semi_open(board: chess.Board, file: int, color: chess.Color) -> bool:
    """ Kiểm tra cột có bán mở (không có Tốt phe mình) không """
    has_friendly_pawn = False
    has_enemy_pawn = False
    opponent = not color
    for rank in range(8):
        piece = board.piece_at(chess.square(file, rank))
        if piece and piece.piece_type == chess.PAWN:
            if piece.color == color:
                has_friendly_pawn = True
                break # Chỉ cần 1 Tốt phe mình là đủ kết luận không bán mở
            else:
                has_enemy_pawn = True
    # Bán mở nếu không có Tốt mình VÀ có Tốt địch (hoặc không có Tốt nào -> open)
    # Định nghĩa phổ biến hơn: bán mở là không có Tốt mình
    return not has_friendly_pawn

def rook_files_tapered(board: chess.Board) -> tuple[int, int]:
    """ Tính điểm bonus cho Xe trên cột mở/bán mở (góc nhìn Trắng) """
    mg_bonus_total = 0
    eg_bonus_total = 0
    white_rooks = board.pieces(chess.ROOK, chess.WHITE)
    black_rooks = board.pieces(chess.ROOK, chess.BLACK)

    for sq in white_rooks:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        is_open = _is_file_open(board, file)
        is_semi_open = _is_file_semi_open(board, file, chess.WHITE)

        if is_open:
            mg_bonus_total += ROOK_OPEN_FILE_BONUS_MG
            eg_bonus_total += ROOK_OPEN_FILE_BONUS_EG
        elif is_semi_open:
            mg_bonus_total += ROOK_SEMI_OPEN_FILE_BONUS_MG
            eg_bonus_total += ROOK_SEMI_OPEN_FILE_BONUS_EG

        # Bonus nếu ở hàng 7 (đối với Trắng)
        if rank == 6: # Rank index 6 là hàng 7
            mg_bonus_total += ROOK_ON_7TH_BONUS_MG
            eg_bonus_total += ROOK_ON_7TH_BONUS_EG

    for sq in black_rooks:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        is_open = _is_file_open(board, file)
        is_semi_open = _is_file_semi_open(board, file, chess.BLACK)

        if is_open:
            mg_bonus_total -= ROOK_OPEN_FILE_BONUS_MG
            eg_bonus_total -= ROOK_OPEN_FILE_BONUS_EG
        elif is_semi_open:
            mg_bonus_total -= ROOK_SEMI_OPEN_FILE_BONUS_MG
            eg_bonus_total -= ROOK_SEMI_OPEN_FILE_BONUS_EG

        # Bonus nếu ở hàng 2 (đối với Đen - rank index 1)
        if rank == 1: # Rank index 1 là hàng 2
            mg_bonus_total -= ROOK_ON_7TH_BONUS_MG # Trừ điểm
            eg_bonus_total -= ROOK_ON_7TH_BONUS_EG

    return mg_bonus_total, eg_bonus_total


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
