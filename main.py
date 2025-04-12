from menu import *
from game import *
from minimax import get_best_move

pygame.init()

screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
pygame.display.set_caption("Chess")

game_mode = get_game_mode(screen)

board = chess.Board()
selected_square = None
legal_moves = []

clock = pygame.time.Clock()
running = True


def handle_game_end():
    update_screen()
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


def player_vs_ai():
    global running, selected_square, legal_moves
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

        elif event_.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event_.pos)

            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
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

def ai_vs_player():
    global running, selected_square, legal_moves
    if board.turn == chess.WHITE and not board.is_game_over():
        best_move = get_best_move(board, depth=3)
        if best_move:
            board.push(best_move)

    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

        elif event_.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event_.pos)

            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)
                if move in board.legal_moves:
                    board.push(move)
                    update_screen()

                selected_square = None
                legal_moves = []

def ai_vs_ai():
    global running
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

    best_move = get_best_move(board, depth=3)
    if best_move:
        board.push(best_move)
        update_screen()

        if not board.is_game_over():
            best_move = get_best_move(board, depth=3)
            if best_move:
                board.push(best_move)

def player_vs_player():
    global running, selected_square, legal_moves
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

        elif event_.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event_.pos)

            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)
                if move in board.legal_moves:
                    board.push(move)
                    update_screen()

                selected_square = None
                legal_moves = []



while running:
    clock.tick(60)
    update_screen()
    if game_mode == TWO_PLAYERS:
        player_vs_player()
    elif game_mode == TWO_AIS:
        ai_vs_ai()
    elif game_mode == PLAYER_VS_AI:
        player_vs_ai()
    elif game_mode == AI_VS_PLAYER:
        ai_vs_player()

pygame.quit()