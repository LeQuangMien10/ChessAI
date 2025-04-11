from config import *
from game import *
from minimax import get_best_move

pygame.init()

screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
pygame.display.set_caption("Chess")

board = chess.Board()
selected_square = None
legal_moves = []

running = True


def handle_game_end():
    result = "Checkmate" if board.is_checkmate() else "Draw"
    font = pygame.font.Font(None, 32)
    text = font.render(result, True, (0, 0, 0))
    screen.blit(text, (BOARD_SIZE // 2 - 50, BOARD_SIZE // 2))
    pygame.display.flip()
    pygame.time.wait(2000)


def update_screen():
    screen.fill((0, 0, 0))
    draw_board(screen, selected_square, legal_moves)
    draw_pieces(screen, board)
    pygame.display.flip()


while running:
    update_screen()

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
                    update_screen()

                    if not board.is_game_over():
                        best_move = get_best_move(board, depth=3)
                        if best_move:
                            board.push(best_move)

                selected_square = None
                legal_moves = []

    if board.is_game_over():
        handle_game_end()
        running = False

pygame.quit()