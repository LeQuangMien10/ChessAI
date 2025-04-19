import chess

# Các hằng số (sẽ được điều chỉnh theo giai đoạn)
BISHOP_PAIR_BONUS = 40
BAD_BISHOP_PAWN_PENALTY = -15
TRAPPED_BISHOP_PENALTY = -75
FIANCHETTO_BONUS = 15
COLOR_WEAKNESS_RELATED_PENALTY = -10
UNDEFENDED_BISHOP_PENALTY = -25
RETURNING_BISHOP_PENALTY = -10
MOBILITY_BONUS = 2

CENTRAL_SQUARES = {chess.D4, chess.E4, chess.D5, chess.E5}
FIANCHETTO_SQUARES = {chess.B2, chess.G2, chess.B7, chess.G7}
BISHOP_TRAP_SQUARES_WHITE = {chess.A2, chess.H2, chess.A3, chess.H3}
BISHOP_TRAP_SQUARES_BLACK = {chess.A7, chess.H7, chess.A6, chess.H6}
BISHOP_TRAP_ESCAPE_WHITE = {chess.A2: chess.B3, chess.H2: chess.G3, chess.A3: chess.B4, chess.H3: chess.G4}
BISHOP_TRAP_ESCAPE_BLACK = {chess.A7: chess.B6, chess.H7: chess.G6, chess.A6: chess.B5, chess.H6: chess.G5}

def get_square_color_numeric(square):
    return (chess.square_rank(square) + chess.square_file(square)) % 2


def preprocess_pawn_structure(board):
    white_pawns = list(board.pieces(chess.PAWN, chess.WHITE))
    black_pawns = list(board.pieces(chess.PAWN, chess.BLACK))
    pawn_info = {
        'white': {'light': 0, 'dark': 0, 'central_light': 0, 'central_dark': 0},
        'black': {'light': 0, 'dark': 0, 'central_light': 0, 'central_dark': 0}
    }
    for pawn_sq in white_pawns:
        color = get_square_color_numeric(pawn_sq)
        pawn_info['white']['light' if color == 0 else 'dark'] += 1
        if pawn_sq in CENTRAL_SQUARES:
            pawn_info['white']['central_light' if color == 0 else 'central_dark'] += 1
    for pawn_sq in black_pawns:
        color = get_square_color_numeric(pawn_sq)
        pawn_info['black']['light' if color == 0 else 'dark'] += 1
        if pawn_sq in CENTRAL_SQUARES:
            pawn_info['black']['central_light' if color == 0 else 'central_dark'] += 1
    return pawn_info

def is_fianchetto_supported(board, square, color):
    if color == chess.WHITE:
        if square == chess.G2:
            return (board.piece_at(chess.H3) == chess.Piece(chess.PAWN, chess.WHITE) and
                    board.piece_at(chess.F3) == chess.Piece(chess.PAWN, chess.WHITE))
        if square == chess.B2:
            return (board.piece_at(chess.A3) == chess.Piece(chess.PAWN, chess.WHITE) and
                    board.piece_at(chess.C3) == chess.Piece(chess.PAWN, chess.WHITE))
    else:
        if square == chess.G7:
            return (board.piece_at(chess.H6) == chess.Piece(chess.PAWN, chess.BLACK) and
                    board.piece_at(chess.F6) == chess.Piece(chess.PAWN, chess.BLACK))
        if square == chess.B7:
            return (board.piece_at(chess.A6) == chess.Piece(chess.PAWN, chess.BLACK) and
                    board.piece_at(chess.C6) == chess.Piece(chess.PAWN, chess.BLACK))
    return False

def evaluate_bishop_specifics(board):
    score = 0
    white_bishops = list(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = list(board.pieces(chess.BISHOP, chess.BLACK))
    num_white_bishops = len(white_bishops)
    num_black_bishops = len(black_bishops)
    pawn_info = preprocess_pawn_structure(board)

    # Điều chỉnh hằng số theo giai đoạn
    scores = {
        'BISHOP_PAIR_BONUS': 40, 'BAD_BISHOP_PAWN_PENALTY': -20,
        'TRAPPED_BISHOP_PENALTY': -75, 'FIANCHETTO_BONUS': 15,
        'COLOR_WEAKNESS_RELATED_PENALTY': -10, 'UNDEFENDED_BISHOP_PENALTY': -25,
        'RETURNING_BISHOP_PENALTY': -10, 'MOBILITY_BONUS': 2
    }

    # Bishop Pair
    if num_white_bishops >= 2:
        score += scores['BISHOP_PAIR_BONUS']
    if num_black_bishops >= 2:
        score -= scores['BISHOP_PAIR_BONUS']

    # Đánh giá Tượng Trắng
    for square in white_bishops:
        bishop_score = 0
        bishop_sq_color = get_square_color_numeric(square)

        # Bad Bishop
        bad_pawn_count = pawn_info['white']['central_light' if bishop_sq_color == 0 else 'central_dark']
        bishop_score += bad_pawn_count * scores['BAD_BISHOP_PAWN_PENALTY']

        # Trapped Bishop
        if square in BISHOP_TRAP_SQUARES_WHITE:
            escape_sq = BISHOP_TRAP_ESCAPE_WHITE.get(square)
            if escape_sq and board.piece_at(escape_sq) == chess.Piece(chess.PAWN, chess.BLACK):
                bishop_score += scores['TRAPPED_BISHOP_PENALTY']
            valid_moves = len(list(board.attacks(square)))
            if valid_moves <= 1:
                bishop_score += scores['TRAPPED_BISHOP_PENALTY'] * 0.5

        # Fianchetto
        if square in FIANCHETTO_SQUARES and is_fianchetto_supported(board, square, chess.WHITE):
            bishop_score += scores['FIANCHETTO_BONUS']

        # Returning Bishop
        if chess.square_rank(square) == 0 and square not in FIANCHETTO_SQUARES:
            bishop_score += scores['RETURNING_BISHOP_PENALTY']

        # Color Weakness
        same_color_pawns = pawn_info['white']['light' if bishop_sq_color == 0 else 'dark']
        total_white_pawns = sum(pawn_info['white'].values())
        if total_white_pawns > 0 and same_color_pawns / total_white_pawns > 0.6:
            attack_squares = board.attacks(square)
            different_color_attacks = sum(1 for sq in attack_squares if get_square_color_numeric(sq) != bishop_sq_color)
            if different_color_attacks < 3:
                bishop_score += scores['COLOR_WEAKNESS_RELATED_PENALTY']

        # Undefended Bishop
        if not list(board.attackers(chess.WHITE, square)):
            if list(board.attackers(chess.BLACK, square)):
                bishop_score += scores['UNDEFENDED_BISHOP_PENALTY'] * 1.5
            else:
                bishop_score += scores['UNDEFENDED_BISHOP_PENALTY']

        # Mobility
        mobility = len(list(board.attacks(square)))
        bishop_score += mobility * scores['MOBILITY_BONUS']

        score += bishop_score

    # Đánh giá Tượng Đen
    for square in black_bishops:
        bishop_score = 0
        bishop_sq_color = get_square_color_numeric(square)

        # Bad Bishop
        bad_pawn_count = pawn_info['black']['central_light' if bishop_sq_color == 0 else 'central_dark']
        bishop_score -= bad_pawn_count * scores['BAD_BISHOP_PAWN_PENALTY']

        # Trapped Bishop
        if square in BISHOP_TRAP_SQUARES_BLACK:
            escape_sq = BISHOP_TRAP_ESCAPE_BLACK.get(square)
            if escape_sq and board.piece_at(escape_sq) == chess.Piece(chess.PAWN, chess.WHITE):
                bishop_score -= scores['TRAPPED_BISHOP_PENALTY']
            valid_moves = len(list(board.attacks(square)))
            if valid_moves <= 1:
                bishop_score -= scores['TRAPPED_BISHOP_PENALTY'] * 0.5

        # Fianchetto
        if square in FIANCHETTO_SQUARES and is_fianchetto_supported(board, square, chess.BLACK):
            bishop_score -= scores['FIANCHETTO_BONUS']

        # Returning Bishop
        if chess.square_rank(square) == 7 and square not in FIANCHETTO_SQUARES:
            bishop_score -= scores['RETURNING_BISHOP_PENALTY']

        # Color Weakness
        same_color_pawns = pawn_info['black']['light' if bishop_sq_color == 0 else 'dark']
        total_black_pawns = sum(pawn_info['black'].values())
        if total_black_pawns > 0 and same_color_pawns / total_black_pawns > 0.6:
            attack_squares = board.attacks(square)
            different_color_attacks = sum(1 for sq in attack_squares if get_square_color_numeric(sq) != bishop_sq_color)
            if different_color_attacks < 3:
                bishop_score -= scores['COLOR_WEAKNESS_RELATED_PENALTY']

        # Undefended Bishop
        if not list(board.attackers(chess.BLACK, square)):
            if list(board.attackers(chess.WHITE, square)):
                bishop_score -= scores['UNDEFENDED_BISHOP_PENALTY'] * 1.5
            else:
                bishop_score -= scores['UNDEFENDED_BISHOP_PENALTY']

        # Mobility
        mobility = len(list(board.attacks(square)))
        bishop_score -= mobility * scores['MOBILITY_BONUS']

        score += bishop_score

    return score


if __name__ == "__main__":
    board1 = chess.Board("rn1qk2r/pp2pp1p/3p1np1/8/2BNP3/1PN5/PBP2PPP/R2QK2R w KQkq - 0 6")
    print(f"FEN 1: {board1.fen()}")
    eval1 = evaluate_bishop_specifics(board1)
    print(f"Bishop Evaluation 1: {eval1}")