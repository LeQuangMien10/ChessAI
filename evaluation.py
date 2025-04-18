import chess

from config import *

#HAM TONG
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
    
    evaluation += pawn_structure(board_)
    
    evaluation += mobility(board_)

    return evaluation * color




#material
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

#piece_square_tables
def piece_square_tables(board_):
    """
    Đánh giá vị trí quân cờ theo quân trắng
    :param board_: bàn cờ
    :return: Điểm vị trí các quân cờ theo màu trắng
    """
    evaluation_ = 0
    # positional_bonus = 0
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

# Pawn Structure
def pawn_structure(board_):
    """
    Đánh giá cấu trúc tốt trên bàn cờ theo phía trắng
    """
    evaluation_ = 0
    white_pawns = board_.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board_.pieces(chess.PAWN, chess.BLACK)

    def get_files(pawn_squares):
        return sorted(set([chess.square_file(sq) for sq in pawn_squares]))

    def is_isolated(square, color):
        file = chess.square_file(square)
        neighbor_files = [f for f in [file - 1, file + 1] if 0 <= f <= 7]
        for neighbor_file in neighbor_files:
            for rank in range(8):
                neighbor_square = chess.square(neighbor_file, rank)
                if board_.piece_at(neighbor_square) == chess.Piece(chess.PAWN, color):
                    return False
        return True

    def is_doubled(square, color):
        file = chess.square_file(square)
        count = 0
        for rank in range(8):
            sq = chess.square(file, rank)
            if board_.piece_at(sq) == chess.Piece(chess.PAWN, color):
                count += 1
        return count > 1

    def is_passed(square, color):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        direction = 1 if color == chess.WHITE else -1
        enemy_color = not color

        for f in [file - 1, file, file + 1]:
            if 0 <= f <= 7:
                r = rank + direction
                while 0 <= r <= 7:
                    sq = chess.square(f, r)
                    if board_.piece_at(sq) == chess.Piece(chess.PAWN, enemy_color):
                        return False
                    r += direction
        return True

    def is_backward(square, color):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        direction = 1 if color == chess.WHITE else -1
        enemy_color = not color

        # Không có đồng minh phía sau để đẩy lên
        has_support = False
        for f in [file - 1, file + 1]:
            if 0 <= f <= 7:
                for r in range(rank - direction, rank - direction * 3, -direction):
                    if 0 <= r <= 7:
                        sq = chess.square(f, r)
                        if board_.piece_at(sq) == chess.Piece(chess.PAWN, color):
                            has_support = True
                            break

        if has_support:
            return False

        # Có quân địch kiểm soát ô trước mặt
        front_square = chess.square(file, rank + direction)
        attackers = board_.attackers(enemy_color, front_square)
        return bool(attackers)

    def count_islands(pawn_squares):
        files = sorted([chess.square_file(sq) for sq in pawn_squares])
        if not files:
            return 0
        islands = 1
        for i in range(1, len(files)):
            if files[i] != files[i - 1] + 1:
                islands += 1
        return islands

    for square in white_pawns:
        if is_isolated(square, chess.WHITE):
            evaluation_ -= ISOLATED_PAWN_PENALTY
        if is_doubled(square, chess.WHITE):
            evaluation_ -= DOUBLED_PAWN_PENALTY
        if is_passed(square, chess.WHITE):
            evaluation_ += PASSED_PAWN_BONUS
        if is_backward(square, chess.WHITE):
            evaluation_ -= BACKWARD_PAWN_PENALTY

    for square in black_pawns:
        if is_isolated(square, chess.BLACK):
            evaluation_ += ISOLATED_PAWN_PENALTY
        if is_doubled(square, chess.BLACK):
            evaluation_ += DOUBLED_PAWN_PENALTY
        if is_passed(square, chess.BLACK):
            evaluation_ -= PASSED_PAWN_BONUS
        if is_backward(square, chess.BLACK):
            evaluation_ += BACKWARD_PAWN_PENALTY

    # Đánh giá pawn island
    white_islands = count_islands(white_pawns)
    black_islands = count_islands(black_pawns)
    evaluation_ -= PAWN_ISLAND_PENALTY * (white_islands - 1)
    evaluation_ += PAWN_ISLAND_PENALTY * (black_islands - 1)

    return evaluation_


# Evaluation of Pieces
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

# Center Control


# Connectivity
# Trapped Pieces
# King Safety
# Space
# Tempo