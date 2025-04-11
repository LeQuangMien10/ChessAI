from game import *
from minimax import get_best_move

pygame.init()

screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
pygame.display.set_caption("Chess")

board = chess.Board()
selected_square = None
legal_moves = []

running = True
while running:
    screen.fill((0, 0, 0))
    draw_board(screen, selected_square, legal_moves)
    draw_pieces(screen, board)

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event.pos)

            if selected_square is None:
                piece = board.piece_at(square)
                if piece and piece.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)
                if move in board.legal_moves:
                    board.push(move)
                    draw_board(screen, selected_square, legal_moves)
                    draw_pieces(screen, board)

                    pygame.display.flip()
                    pygame.event.pump()

                    if not board.is_game_over():
                        best_move = get_best_move(board, depth=3)
                        if best_move:
                            board.push(best_move)
                selected_square = None
                legal_moves = []


pygame.quit()