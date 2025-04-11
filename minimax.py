import time

import chess

import config
from config import *

def evaluate_board(board_):
    if board_.is_checkmate():
        return -float('inf') if board_.turn else float('inf')
    if board_.is_stalemate() or board_.is_insufficient_material():
        return 0

    evaluation = 0

    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece:
            value = config.PIECE_VALUES[piece.piece_type]

            positional_bonus = 0
            index = square if piece.color == chess.WHITE else chess.square_mirror(square)

            if piece.piece_type == chess.PAWN:
                positional_bonus = config.PAWN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KNIGHT:
                positional_bonus = config.KNIGHT_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.BISHOP:
                positional_bonus = config.BISHOP_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.ROOK:
                positional_bonus = config.ROOK_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.QUEEN:
                positional_bonus = config.QUEEN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KING:
                positional_bonus = config.KING_POSITION_BONUS[7 - index // 8][index % 8]

            total = value + positional_bonus
            evaluation += total if piece.color == chess.WHITE else -total

    return evaluation

def minimax(board, depth, alpha, beta, is_maximizing):
    if depth == 0 or board.is_game_over():
        evaluation = evaluate_board(board)
        if not is_maximizing:
            return -evaluation
        else:
            return evaluation

    if is_maximizing:
        max_value = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, is_maximizing)
            board.pop()

            max_value = max(max_value, evaluation)
            alpha = max(alpha, evaluation)
            if alpha >= beta:
                break
        return max_value
    else:
        min_value = float('inf')
        for move in board.legal_moves:
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, is_maximizing)
            board.pop()

            min_value = min(min_value, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_value

def get_best_move(board, depth=3):
    start_time = time.time()

    best_move = None
    best_value = -float('inf')

    for move in board.legal_moves:
        board.push(move)
        evaluation = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board.pop()

        if evaluation > best_value:
            best_value = evaluation
            best_move = move


    elapsed_time = time.time() - start_time
    print(f"Time: {elapsed_time: .2f} seconds")

    return best_move


# board = chess.Board()
# print(evaluate_board(board))
# print(board)