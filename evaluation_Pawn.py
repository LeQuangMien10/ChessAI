from collections import defaultdict
import chess
from time import perf_counter
from config import *

def evaluate_pawn_features(board_: chess.Board) -> float:
    evaluation = 0

    CENTER_SQUARES = {chess.D4, chess.E4, chess.D5, chess.E5}

    # constants (tách ra config.py nếu muốn tuning dễ hơn)
    PAWN_CENTER_OCCUPATION_BONUS = 0.4
    PAWN_CENTER_CONTROL_BONUS = 0.2
    BLOCKED_PAWN_PENALTY = 0.3

    for color in [chess.WHITE, chess.BLACK]:
        direction = 1 if color == chess.WHITE else -1
        multiplier = 1 if color == chess.WHITE else -1

        pawn_squares = board_.pieces(chess.PAWN, color)
        files = sorted([chess.square_file(sq) for sq in pawn_squares])

        # Đếm islands
        islands = 0
        if files:
            islands = 1
            for i in range(1, len(files)):
                if files[i] != files[i - 1] + 1:
                    islands += 1
        evaluation -= multiplier * PAWN_ISLAND_PENALTY * (islands - 1)

        for square in pawn_squares:
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            # Center occupation
            if square in CENTER_SQUARES:
                evaluation += multiplier * PAWN_CENTER_OCCUPATION_BONUS
            else:
                attacks = board_.attacks(square)
                if attacks & CENTER_SQUARES:
                    evaluation += multiplier * PAWN_CENTER_CONTROL_BONUS

            # Blocked
            forward_square = square + 8 * direction
            if 0 <= forward_square <= 63:
                blocker = board_.piece_at(forward_square)
                if blocker and blocker.color != color:
                    evaluation -= multiplier * BLOCKED_PAWN_PENALTY

            # Isolated
            isolated = True
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file <= 7:
                    for r in range(8):
                        neighbor_sq = chess.square(adj_file, r)
                        if board_.piece_at(neighbor_sq) == chess.Piece(chess.PAWN, color):
                            isolated = False
                            break
                if not isolated:
                    break
            if isolated:
                evaluation -= multiplier * ISOLATED_PAWN_PENALTY

            # Doubled
            count_same_file = sum(
                1 for r in range(8)
                if board_.piece_at(chess.square(file, r)) == chess.Piece(chess.PAWN, color)
            )
            if count_same_file > 1:
                evaluation -= multiplier * DOUBLED_PAWN_PENALTY

            # Passed pawn
            is_passed = True
            enemy_color = not color
            for f in [file - 1, file, file + 1]:
                if 0 <= f <= 7:
                    r = rank + direction
                    while 0 <= r <= 7:
                        sq = chess.square(f, r)
                        if board_.piece_at(sq) == chess.Piece(chess.PAWN, enemy_color):
                            is_passed = False
                            break
                        r += direction
                if not is_passed:
                    break
            if is_passed:
                evaluation += multiplier * PASSED_PAWN_BONUS

            # Backward pawn
            # Kiểm tra không có đồng minh hỗ trợ và bị tấn công ô trước
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
                    break
            if not has_support:
                front_square = chess.square(file, rank + direction)
                attackers = board_.attackers(enemy_color, front_square)
                if attackers:
                    evaluation -= multiplier * BACKWARD_PAWN_PENALTY

    return evaluation
