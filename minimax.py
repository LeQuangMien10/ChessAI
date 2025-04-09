import math
import time

from pygame_chess_api.api import Board, Move, Piece, Queen, King, Bishop, Rook, Pawn, Knight

# Piece position evaluation tables
PAWN_EVAL_WHITE = Pawn.POSITION_BONUS

PAWN_EVAL_BLACK = list(reversed(PAWN_EVAL_WHITE))

KNIGHT_EVAL = Knight.POSITION_BONUS

BISHOP_EVAL_WHITE = Bishop.POSITION_BONUS

BISHOP_EVAL_BLACK = list(reversed(BISHOP_EVAL_WHITE))

ROOK_EVAL_WHITE = Rook.POSITION_BONUS

ROOK_EVAL_BLACK = list(reversed(ROOK_EVAL_WHITE))

QUEEN_EVAL = Queen.POSITION_BONUS

KING_EVAL_WHITE = King.POSITION_BONUS

KING_EVAL_BLACK = list(reversed(KING_EVAL_WHITE))

def evaluate_board(board: Board) -> float:
    """Evaluate the board position from the perspective of the current player"""
    total_evaluation = 0
    
    for pos, piece in board.pieces_by_pos.items():
        x, y = pos
        piece_value = 0
        
        # Base piece value
        piece_value += piece.SCORE_VALUE
        
        # Position bonus
        if isinstance(piece, Pawn):
            piece_value += PAWN_EVAL_WHITE[y][x] if piece.color == Piece.WHITE else PAWN_EVAL_BLACK[y][x]
        elif isinstance(piece, Knight):
            piece_value += KNIGHT_EVAL[y][x]
        elif isinstance(piece, Bishop):
            piece_value += BISHOP_EVAL_WHITE[y][x] if piece.color == Piece.WHITE else BISHOP_EVAL_BLACK[y][x]
        elif isinstance(piece, Rook):
            piece_value += ROOK_EVAL_WHITE[y][x] if piece.color == Piece.WHITE else ROOK_EVAL_BLACK[y][x]
        elif isinstance(piece, Queen):
            piece_value += QUEEN_EVAL[y][x]
        elif isinstance(piece, King):
            piece_value += KING_EVAL_WHITE[y][x] if piece.color == Piece.WHITE else KING_EVAL_BLACK[y][x]
        
        # Adjust for color
        if piece.color == board.cur_color_turn:
            total_evaluation += piece_value
        else:
            total_evaluation -= piece_value
    
    return total_evaluation

def minimax(board: Board, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """Minimax algorithm with alpha-beta pruning"""
    if depth == 0 or board.game_ended:
        return evaluate_board(board)
    
    if maximizing_player:
        max_eval = float('-inf')
        for pos, piece in board.pieces_by_pos.items():
            if piece.color == board.cur_color_turn:
                moves = piece.get_moves_allowed()
                for move in moves:
                    # Create a copy of the board for the move
                    new_board = board.create_hypothesis_board()
                    new_piece = new_board.pieces_by_pos[pos]
                    
                    # Handle pawn promotion
                    if isinstance(piece, Pawn) and move.special_type == Move.TO_PROMOTE_TYPE:
                        new_piece.promote_class_wanted = Queen  # Always promote to queen for simplicity
                    
                    # Make the move
                    new_board.move_piece(new_piece, move)
                    
                    # Recursive call
                    eval = minimax(new_board, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for pos, piece in board.pieces_by_pos.items():
            if piece.color == board.cur_color_turn:
                moves = piece.get_moves_allowed()
                for move in moves:
                    # Create a copy of the board for the move
                    new_board = board.create_hypothesis_board()
                    new_piece = new_board.pieces_by_pos[pos]
                    
                    # Handle pawn promotion
                    if isinstance(piece, Pawn) and move.special_type == Move.TO_PROMOTE_TYPE:
                        new_piece.promote_class_wanted = Queen  # Always promote to queen for simplicity
                    
                    # Make the move
                    new_board.move_piece(new_piece, move)
                    
                    # Recursive call
                    eval = minimax(new_board, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval

def get_best_move(board: Board, depth: int) -> tuple[Piece, Move]:
    """Get the best move for the current player using minimax"""
    start_time = time.time()

    best_move = None
    best_piece = None
    best_eval = float('-inf')
    
    for pos, piece in board.pieces_by_pos.items():
        if piece.color == board.cur_color_turn:
            moves = piece.get_moves_allowed()
            for move in moves:
                # Create a copy of the board for the move
                new_board = board.create_hypothesis_board()
                new_piece = new_board.pieces_by_pos[pos]
                
                # Handle pawn promotion
                if isinstance(piece, Pawn) and move.special_type == Move.TO_PROMOTE_TYPE:
                    new_piece.promote_class_wanted = Queen  # Always promote to queen for simplicity
                
                # Make the move
                new_board.move_piece(new_piece, move)
                
                # Evaluate the move
                eval = minimax(new_board, depth - 1, float('-inf'), float('inf'), False)
                
                if eval > best_eval:
                    best_eval = eval
                    best_move = move
                    best_piece = piece

    elapsed_time = time.time() - start_time
    print(f"Thời gian tính toán: {elapsed_time:.2f} giây")

    return best_piece, best_move

def function_for_ai(board: Board) -> None:
    """Function to be called by the GUI for AI moves"""
    piece, move = get_best_move(board, depth=3)  # You can adjust the depth here
    print(f"AI move: {piece} to {move.target}")
    piece.move(move) 