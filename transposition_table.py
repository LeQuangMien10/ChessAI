import chess
import random

def init_zobrist_table(seed=0):
    """Khởi tạo bảng Zobrist với seed cho tính tái lập."""
    random.seed(seed)
    global ZORBIST_TABLE, ZORBIST_BLACK_TO_MOVE, ZORBIST_CASTLING, ZORBIST_EN_PASSANT
    ZORBIST_TABLE = [[random.getrandbits(64) for _ in range(12)] for _ in range(64)]
    ZORBIST_BLACK_TO_MOVE = random.getrandbits(64)
    ZORBIST_CASTLING = [random.getrandbits(64) for _ in range(16)]  # 2^4 trạng thái nhập thành
    ZORBIST_EN_PASSANT = [random.getrandbits(64) for _ in range(8)]  # 8 cột

# Khởi tạo bảng Zobrist với seed mặc định
init_zobrist_table(seed=0)

def compute_zorbist_hash(board: chess.Board) -> int:
    """
    Tính Zobrist hash cho trạng thái bàn cờ.

    Args:
        board: Đối tượng chess.Board đại diện cho trạng thái bàn cờ.

    Returns:
        Giá trị băm 64-bit duy nhất cho trạng thái bàn cờ.

    Raises:
        ValueError: Nếu board không phải là đối tượng chess.Board.
    """
    if not isinstance(board, chess.Board):
        raise ValueError("Input must be a chess.Board object")

    zorbist_hash = 0

    # Xử lý quân cờ
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_index = piece.piece_type - 1  # 0-5 cho Trắng (Tốt, Mã, Tượng, Xe, Hậu, Vua)
            if piece.color == chess.BLACK:
                piece_index += 6  # 6-11 cho Đen
            zorbist_hash ^= ZORBIST_TABLE[square][piece_index]

    # Xử lý lượt đi
    if board.turn == chess.BLACK:
        zorbist_hash ^= ZORBIST_BLACK_TO_MOVE

    # Xử lý quyền nhập thành
    castling_index = (
        (1 if board.has_kingside_castling_rights(chess.WHITE) else 0) << 0 |
        (1 if board.has_queenside_castling_rights(chess.WHITE) else 0) << 1 |
        (1 if board.has_kingside_castling_rights(chess.BLACK) else 0) << 2 |
        (1 if board.has_queenside_castling_rights(chess.BLACK) else 0) << 3
    )
    zorbist_hash ^= ZORBIST_CASTLING[castling_index]

    # Xử lý bắt qua đường
    if board.ep_square is not None:
        ep_column = chess.square_file(board.ep_square)
        zorbist_hash ^= ZORBIST_EN_PASSANT[ep_column]

    return zorbist_hash