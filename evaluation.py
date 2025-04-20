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

#Tạm thời giữ như vậy
EVAL_WEIGHTS = {
    'material': 1.00,             # cơ bản, nên là trọng số chuẩn
    'piece_square_tables': 0.15,  # PST chỉ là điều chỉnh vị trí
    'pawn_structure': 0.25,       # khá quan trọng (tốt cô lập, backward, island)
    'mobility': 0.20,             # ảnh hưởng chiến lược trung cuộc
    'king_safety': 0.40,          # rất quan trọng trung cuộc
    'trapped_pieces': 0.15,       # nhẹ, vì hiếm gặp
    'space': 0.25,                # quan trọng trung cuộc, nhất là với minor pieces
    'mop_up': 0.30                # dùng chủ yếu ở endgame
}
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
    phase = get_game_phase(board_) # Giá trị từ 0 (EG) đến 256 (MG)

    # --- Tính Điểm MG/EG cho Từng Thành Phần ---
    mg_material, eg_material = material(board_)
    mg_pst, eg_pst = piece_square_tables(board_)

    # --- (Ví dụ nếu bạn thêm lại các hàm khác) ---
    # mg_king_safety, eg_king_safety = king_safety(board_) # Cần hàm trả về tuple
    # mg_passed_pawns, eg_passed_pawns = passed_pawns_eval(board_) # Cần hàm trả về tuple
    # mg_rook_files, eg_rook_files = rook_files_eval(board_)
    # ... các thành phần khác ...


    # --- Nội Suy Điểm Cuối Cùng ---
    final_material = interpolate(mg_material, eg_material, phase)
    final_pst = interpolate(mg_pst, eg_pst, phase)

    # --- (Ví dụ nội suy các thành phần khác) ---
    # final_king_safety = interpolate(mg_king_safety, eg_king_safety, phase)
    # final_passed_pawns = interpolate(mg_passed_pawns, eg_passed_pawns, phase)
    # final_rook_files = interpolate(mg_rook_files, eg_rook_files, phase)

    # --- Tính Tổng Đánh Giá (Áp dụng trọng số nếu muốn) ---
    # Ví dụ: chỉ có material và PST
    # total_eval = (final_material * 1.0) + (final_pst * 1.0) # Bỏ trọng số phức tạp ban đầu đi
    total_eval = (final_material * EVAL_WEIGHTS['material']) + (final_pst * EVAL_WEIGHTS['piece_square_tables']) # Bỏ trọng số phức tạp ban đầu đi
    # total_eval = (final_material * material_weight) + \
    #              (final_pst * piece_square_tables_weight) + \
    #              (final_king_safety * king_safety_weight) + \
    #              (final_passed_pawns * passed_pawns_weight) + \
    #              (final_rook_files * rook_files_weight)
                 # ... cộng các thành phần đã nội suy khác ...

    # --- Trả về điểm cuối cùng (theo góc nhìn Trắng) ---
    # Hàm negamax sẽ tự xử lý perspective_multiplier
    return int(total_eval) # Trả về số nguyên
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
                row, col = divmod(index, 8) # Hoặc dùng 7 - index // 8, index % 8 như cũ
                row_idx = 7 - row # Vì bảng thường định nghĩa từ rank 8 xuống 1

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
