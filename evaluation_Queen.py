from config import *

EARLY_QUEEN_DEVELOPMENT_PENALTY = 15 # Phạt nếu Hậu ra trận khi quân nhẹ chưa phát triển hết

def has_undeveloped_minor_pieces(board: chess.Board, color: chess.Color) -> bool:
    """Kiểm tra xem còn quân nhẹ (Mã/Tượng) chưa phát triển khỏi vị trí ban đầu không."""
    start_rank = chess.BB_RANK_1 if color == chess.WHITE else chess.BB_RANK_8
    # Các ô xuất phát của quân nhẹ
    knight_starts = (chess.B1 | chess.G1) if color == chess.WHITE else (chess.B8 | chess.G8)
    bishop_starts = (chess.C1 | chess.F1) if color == chess.WHITE else (chess.C8 | chess.F8)

    # Kiểm tra Mã
    for sq in chess.scan_reversed(knight_starts): # Dùng scan_reversed để duyệt qua các bit trong bitboard
        p = board.piece_at(sq)
        if p and p.piece_type == chess.KNIGHT and p.color == color:
            return True # Tìm thấy Mã chưa phát triển

    # Kiểm tra Tượng
    for sq in chess.scan_reversed(bishop_starts):
        p = board.piece_at(sq)
        if p and p.piece_type == chess.BISHOP and p.color == color:
            return True # Tìm thấy Tượng chưa phát triển

    return False # Không còn quân nhẹ nào ở vị trí ban đầu

def evaluate_queens(board: chess.Board, color: chess.Color) -> int:
    """ Tính điểm vị trí cho tất cả các Hậu của phe 'color'. """
    queen_score = 0
    queen_squares = board.pieces(chess.QUEEN, color)
    # Lấy tất cả nước đi hợp lệ một lần để tối ưu tính mobility
    # Lưu ý: Tính board.legal_moves có thể tốn kém, nhưng thường chỉ cần 1 lần/evaluation
    legal_moves = list(board.legal_moves)

    # Xác định ô xuất phát của Hậu
    queen_start_square = chess.D1 if color == chess.WHITE else chess.D8

    # Kiểm tra xem có quân nhẹ chưa phát triển không (chỉ cần làm 1 lần)
    check_early_dev = has_undeveloped_minor_pieces(board, color)

    for square in queen_squares:

        # 1. Tính Mobility
        queen_mobility = 0
        for move in legal_moves:
            if move.from_square == square:
                queen_mobility += 1

        mobility_bonus = int(queen_mobility * MOBILITY_WEIGHTS.get(chess.QUEEN, 0))
        queen_score += mobility_bonus

        # 2. Phạt Phát triển sớm
        if check_early_dev and square != queen_start_square:
             # Nếu còn quân nhẹ chưa ra và Hậu đã di chuyển khỏi ô ban đầu
             queen_score -= EARLY_QUEEN_DEVELOPMENT_PENALTY

    return queen_score