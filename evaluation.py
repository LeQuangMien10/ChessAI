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

def get_phase_ratio(board):
    phase = TOTAL_PHASE
    for piece_type in PIECE_PHASE:
        count = len(board.pieces(piece_type, chess.WHITE)) + len(board.pieces(piece_type, chess.BLACK))
        phase -= PIECE_PHASE[piece_type] * count
    return max(0, min(1, phase / TOTAL_PHASE))  # clamp trong [0,1]

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
    phase_ratio = get_phase_ratio(board_)
    timers = {}

    def time_call(label, func):
        start = perf_counter()
        result = func()
        end = perf_counter()
        timers[label] = end - start
        return result

    eval_components = {}

    eval_components['material'] = material(board_) * EVAL_WEIGHTS['material']
    eval_components['piece_square_tables'] = piece_square_tables(board_) * EVAL_WEIGHTS['piece_square_tables']
    eval_components['mobility'] = mobility(board_) * EVAL_WEIGHTS['mobility']
    eval_components['trapped_pieces'] = trapped_pieces(board_) * EVAL_WEIGHTS['trapped_pieces']
    eval_components['space'] = space(board_) * EVAL_WEIGHTS['space']
    eval_components['evaluate_pieces'] = evaluate_pieces(board_)



    # eval_components['material'] = time_call("material", lambda: material(board_)) * EVAL_WEIGHTS['material']
    # eval_components['piece_square_tables'] = time_call("piece_square_tables", lambda: piece_square_tables(board_)) * EVAL_WEIGHTS['piece_square_tables']
    # eval_components['mobility'] = time_call("mobility", lambda: mobility(board_)) * EVAL_WEIGHTS['mobility']
    # eval_components['trapped_pieces'] = time_call("trapped_pieces", lambda: trapped_pieces(board_)) * EVAL_WEIGHTS['trapped_pieces']
    # eval_components['space'] = time_call("space", lambda: space(board_)) * EVAL_WEIGHTS['space']
    # eval_components['evaluate_pieces'] = time_call("evaluate_pieces", lambda: evaluate_pieces(board_))

    # if phase_ratio < 0.3:
    #     eval_components['mop_up'] = time_call("mop_up", lambda: mop_up_evaluation(board_, chess.WHITE if color == 1 else chess.BLACK)) * EVAL_WEIGHTS['mop_up']
    # else:
    #     eval_components['mop_up'] = 0

    evaluation = sum(eval_components.values())

    # print("\u26a1 Evaluation Benchmark")
    # for label, t in timers.items():
    #     print(f"  {label:18s}: {t:.6f} s")

    return evaluation
# material
def material(board_):
    """
    Đánh giá material theo quân trắng.
    :param board_: bàn cờ
    :return: điểm nguyên liệu theo quân trắng
    """
    value = 0
    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece:
            value += PIECE_VALUES[piece.piece_type] if piece.color == chess.WHITE else -PIECE_VALUES[piece.piece_type]

    return value


# piece_square_tables
def piece_square_tables(board_):
    """
    Đánh giá vị trí quân cờ theo quân trắng
    :param board_: bàn cờ
    :return: Điểm vị trí các quân cờ theo màu trắng
    """
    evaluation_ = 0
    positional_bonus = 0
    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece:
            index = square if piece.color == chess.WHITE else chess.square_mirror(square)

            if piece.piece_type == chess.PAWN:
                positional_bonus = PAWN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KNIGHT:
                positional_bonus = KNIGHT_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.BISHOP:
                positional_bonus = BISHOP_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.ROOK:
                positional_bonus = ROOK_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.QUEEN:
                positional_bonus = QUEEN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KING:
                positional_bonus = KING_POSITION_BONUS[7 - index // 8][index % 8]

            evaluation_ += positional_bonus if piece.color == chess.WHITE else -positional_bonus

    return evaluation_
# Evaluation of Pieces
def evaluate_pieces(board_: chess.Board) -> float:
    """
    Tổng hợp đánh giá các loại quân trên bàn cờ
    """
    evaluation = 0
    phase_ratio = get_phase_ratio(board_)

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
