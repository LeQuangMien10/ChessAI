from collections import defaultdict
import chess
from time import perf_counter

from config import *

def evaluate_king_features(board_: chess.Board, phase_ratio: float) -> float:
    evaluation = 0

    # Configurable constants
    KING_CENTER_ENDGAME_BONUS = 0.3
    KING_WING_NO_PAWN_PENALTY = 0.5
    MATE_THREAT_BONUS = 1.0
    PIN_PENALTY = 0.4
    PAWN_SHIELD_BONUS = 0.2
    KING_ATTACKED_SQUARE_PENALTY = 0.5
    CASTLING_RIGHTS_BONUS = 0.3

    FILE_AH = {0, 7}
    piece_map = board_.piece_map()

    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        king_sq = board_.king(color)

        if king_sq is None:
            evaluation += -10000 * multiplier
            continue

        file = chess.square_file(king_sq)
        rank = chess.square_rank(king_sq)

        # === MIDGAME: King Safety ===
        if phase_ratio >= 0.3:
            # Tính các ô xung quanh
            surrounding = [
                chess.square(f, r)
                for f in range(file - 1, file + 2)
                for r in range(rank - 1, rank + 2)
                if 0 <= f <= 7 and 0 <= r <= 7 and chess.square(f, r) != king_sq
            ]

            # Ô bị tấn công quanh vua
            attackers_around = sum(
                1 for sq in surrounding if board_.attackers(not color, sq)
            )
            evaluation -= multiplier * attackers_around * KING_ATTACKED_SQUARE_PENALTY

            # Tốt bảo vệ quanh vua
            pawn_shield = sum(
                1 for sq in surrounding
                if piece_map.get(sq) == chess.Piece(chess.PAWN, color)
            )
            evaluation += multiplier * pawn_shield * PAWN_SHIELD_BONUS

            # Quyền nhập thành
            if board_.has_kingside_castling_rights(color) or board_.has_queenside_castling_rights(color):
                evaluation += multiplier * CASTLING_RIGHTS_BONUS

            # Mate-at-a-glance: vua gần biên và bị quân mạnh địch tấn công
            if (color == chess.WHITE and rank <= 1) or (color == chess.BLACK and rank >= 6):
                threat_count = sum(
                    1
                    for sq, piece in piece_map.items()
                    if piece.color != color and piece.piece_type in [chess.QUEEN, chess.ROOK]
                    and king_sq in board_.attacks(sq)
                )
                evaluation -= multiplier * threat_count * MATE_THREAT_BONUS

            # X-ray / pin sơ bộ
            for sq, piece in piece_map.items():
                if piece.color == color and piece.piece_type != chess.KING:
                    if king_sq in board_.attackers(color, sq) and board_.attackers(not color, sq):
                        evaluation -= multiplier * PIN_PENALTY
                        break  # chỉ cần 1 là đủ

        # === ENDGAME: King Activity ===
        if phase_ratio < 0.4:
            # Trung tâm hóa
            center_dist = CENTER_MANHATTAN_DISTANCE[7 - rank][file]
            evaluation -= multiplier * KING_CENTER_ENDGAME_BONUS * center_dist

            # Đứng ở cánh không có tốt
            if file in FILE_AH:
                has_wing_pawn = any(
                    piece_map.get(chess.square(file, r)) == chess.Piece(chess.PAWN, color)
                    for r in range(8)
                )
                if not has_wing_pawn:
                    evaluation -= multiplier * KING_WING_NO_PAWN_PENALTY

    return evaluation

