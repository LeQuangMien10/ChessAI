from collections import defaultdict
import chess
from time import perf_counter

from config import *

def evaluate_knight_features(board_: chess.Board) -> float:
    evaluation = 0
    KNIGHT_BASE_VALUE = 300
    PAWN_COUNT_FACTOR = 0.02
    OUTPOST_BONUS = 0.4
    DEFENDED_BY_PAWN_BONUS = 0.2
    UNDEFENDED_PENALTY = 0.3
    BLOCK_C_PAWN_PENALTY = 1.0  # tăng penalty
    TRAPPED_KNIGHT_PENALTY = 1.5

    TRAPPED_KNIGHT_SQUARES = {
        chess.A1, chess.H1, chess.A8, chess.H8,
        chess.A2, chess.H2, chess.A7, chess.H7
    }

    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        knights = board_.pieces(chess.KNIGHT, color)
        pawns = board_.pieces(chess.PAWN, color)
        enemy_pawns = board_.pieces(chess.PAWN, not color)

        pawn_count = len(pawns)
        knight_value = KNIGHT_BASE_VALUE * (1.0 - (8 - pawn_count) * PAWN_COUNT_FACTOR)

        for knight_sq in knights:
            evaluation += multiplier * knight_value

            # Trapped knight
            if knight_sq in TRAPPED_KNIGHT_SQUARES:
                evaluation -= multiplier * TRAPPED_KNIGHT_PENALTY

            # Mobility (trừ ô bị kiểm soát bởi tốt địch)
            mobility_score = 0
            for target in board_.attacks(knight_sq):
                target_piece = board_.piece_at(target)
                if not target_piece or target_piece.color != color:
                    if not any(target in board_.attacks(p) for p in enemy_pawns):
                        mobility_score += 1
            evaluation += multiplier * 0.1 * mobility_score

            # Outpost
            rank = chess.square_rank(knight_sq)
            if (color == chess.WHITE and rank >= 4) or (color == chess.BLACK and rank <= 3):
                if not any(knight_sq in board_.attacks(p) for p in enemy_pawns):
                    evaluation += multiplier * OUTPOST_BONUS

            # Được bảo vệ bởi tốt
            defenders = board_.attackers(color, knight_sq)
            if any(board_.piece_at(sq) == chess.Piece(chess.PAWN, color) for sq in defenders):
                evaluation += multiplier * DEFENDED_BY_PAWN_BONUS

            # Không được bảo vệ
            if len(defenders) == 0:
                evaluation -= multiplier * UNDEFENDED_PENALTY

            # Cản trở tốt C-pawn (Crafty)
            if color == chess.WHITE and knight_sq == chess.C3:
                if chess.C2 in pawns and chess.D4 in pawns and chess.E4 not in pawns:
                    evaluation -= multiplier * BLOCK_C_PAWN_PENALTY
            elif color == chess.BLACK and knight_sq == chess.C6:
                if chess.C7 in pawns and chess.D5 in pawns and chess.E5 not in pawns:
                    evaluation -= multiplier * BLOCK_C_PAWN_PENALTY

    return evaluation
