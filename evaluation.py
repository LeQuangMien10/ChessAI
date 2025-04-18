import chess

from config import *

def evaluate_position(board_, color):
    """
    Đánh giá bàn cờ theo góc nhìn AI
    :param board_: bàn cờ
    :param color: 1 cho trắng, -1 cho đen
    :return:
    """
    evaluation = 0

    if board_.is_checkmate():
        return -float('inf')
    if board_.is_stalemate() or board_.is_insufficient_material() or board_.is_seventyfive_moves() or board_.is_fivefold_repetition():
        return 0  # Hòa, trả về 0

    evaluation += material(board_)

    evaluation += piece_square_tables(board_)

    return evaluation * color

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

    return positional_bonus

# Pawn Structure
# Evaluation of Pieces
# Evaluation Patterns
# Mobility
# Center Control
# Connectivity
# Trapped Pieces
# King Safety
# Space
# Tempo