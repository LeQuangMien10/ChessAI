from config import *
from evaluation import evaluate_position


def negamax(board, depth, alpha, beta, color):
    if depth == 0 or board.is_game_over():
        return color * evaluate_position(board, ai_color_=board.turn if color == 1 else not board.turn)

    max_score = float('-inf')
    for move in board.legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()

        max_score = max(max_score, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    return max_score


def get_best_move(board, depth):
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    color = 1 if board.turn == chess.WHITE else -1

    for move in board.legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    return best_move


# Ví dụ sử dụng
if __name__ == "__main__":
    board = chess.Board()
    depth = 3
    best_move = get_best_move(board, depth)
    print(f"Best move: {best_move}")