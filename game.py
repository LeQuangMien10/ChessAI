from config import *

# Load ảnh quân cờ
pieces = {}
for piece in chess.PIECE_SYMBOLS[1:]:  # 'p', 'n', 'b', 'r', 'q', 'k'
    pieces[piece] = pygame.image.load(f"images/{piece}.png")
    pieces[piece.upper()] = pygame.image.load(f"images/{piece.upper()}_.png")


# Hàm vẽ bàn cờ
def draw_board(screen, selected_square=None, legal_moves=None):
    if legal_moves is None:
        legal_moves = []

    font = pygame.font.SysFont(None, 24)  # Có thể đổi font, size tuỳ ý

    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            if selected_square == chess.square(col, 7 - row):
                color = HIGHLIGHT
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

            # Vẽ ký hiệu cột (a–h) ở hàng cuối cùng
            if row == 7:
                label = font.render(chr(ord('a') + col), True, (0, 0, 0) if color == WHITE else (255, 255, 255))
                screen.blit(label, (col * SQUARE_SIZE + 4, 8 * SQUARE_SIZE - 20))

            # Vẽ ký hiệu hàng (1–8) ở cột đầu tiên
            if col == 0:
                label = font.render(str(8 - row), True, (0, 0, 0) if color == WHITE else (255, 255, 255))
                screen.blit(label, (4, row * SQUARE_SIZE + 4))

    # Highlight các nước đi hợp lệ
    for move in legal_moves:
        col, row = chess.square_file(move), chess.square_rank(move)
        pygame.draw.circle(screen, MOVE_HIGHLIGHT[:3],
                           (col * SQUARE_SIZE + SQUARE_SIZE // 2, (7 - row) * SQUARE_SIZE + SQUARE_SIZE // 2), 10)



# Hàm vẽ quân cờ
def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece_ = board.piece_at(square)
        if piece_:
            row, col = divmod(square, 8)
            screen.blit(pieces[piece_.symbol()], (col * SQUARE_SIZE, (7 - row) * SQUARE_SIZE))


def get_square_from_mouse(pos):
    col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
    return chess.square(col, 7 - row)


def promote_pawn(board, move, screen):
    """Kiểm tra nếu quân tốt đi đến hàng cuối và yêu cầu phong cấp bằng Pygame."""
    piece_ = board.piece_at(move.from_square)

    if piece_ and piece_.piece_type == chess.PAWN:
        last_rank = 7 if piece_.color == chess.WHITE else 0  # Lấy hàng cuối cùng cho từng màu
        if chess.square_rank(move.to_square) == last_rank:  # Kiểm tra tốt đã đến hàng cuối chưa
            color = "white" if piece_.color == chess.WHITE else "black"
            promotion_choice = choose_promotion_pygame(screen, color)
            move.promotion = promotion_choice


def choose_promotion_onlyQ():
    """Hiển thị lựa chọn quân phong cấp, trả về mã quân cờ (hậu, xe, mã, tượng)."""
    # Ở đây ta mặc định phong cấp thành Hậu (Queen)
    return chess.QUEEN


def choose_promotion_pygame(screen, colorTurn):
    """Hiển thị menu chọn quân phong cấp bằng hình ảnh trong Pygame."""
    choices_for_white = {
        "Q": (chess.QUEEN, "images/Q_.png"),
        "R": (chess.ROOK, "images/R_.png"),
        "B": (chess.BISHOP, "images/B_.png"),
        "N": (chess.KNIGHT, "images/N_.png")
    }
    choices_for_black = {
        "Q": (chess.QUEEN, "images/q.png"),
        "R": (chess.ROOK, "images/r.png"),
        "B": (chess.BISHOP, "images/b.png"),
        "N": (chess.KNIGHT, "images/n.png")
    }
    if colorTurn == "black":
        choices = choices_for_black
    else:
        choices = choices_for_white

        # Tạo vùng hiển thị menu
    menu_rect = pygame.Rect(90, 140, 280, 80)
    pygame.draw.rect(screen, (220, 220, 220), menu_rect, border_radius=10)  # Bo góc nhẹ

    # Load ảnh và hiển thị lên màn hình
    button_rects = []
    x_offset = 105
    y_offset = 155
    for key, (piece_, img_path) in choices.items():
        img = pygame.image.load(img_path)
        img = pygame.transform.scale(img, (50, 50))  # Điều chỉnh kích thước ảnh

        btn_rect = screen.blit(img, (x_offset, y_offset))
        button_rects.append((btn_rect, piece_))

        x_offset += 65  # Dịch chuyển ảnh tiếp theo

    pygame.display.flip()

    # Chờ người chơi chọn quân phong cấp
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn_rect, piece_ in button_rects:
                    if btn_rect.collidepoint(event.pos):
                        return piece_
