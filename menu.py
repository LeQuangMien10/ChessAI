from config import *


def draw_menu(screen):
    screen.fill((255, 255, 255))
    font = pygame.font.Font(None, 48)

    modes = {
        TWO_PLAYERS: "Two Players",
        TWO_AIS: "Two AIs",
        PLAYER_VS_AI: "Player White, AI Black",
        AI_VS_PLAYER: "AI White, Player Black"
    }

    buttons = []
    for i in modes.keys():
        text = font.render(modes[i], True, (0, 0, 0))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, 100 + i * 100))
        screen.blit(text, rect)
        buttons.append((rect, i))

    pygame.display.flip()
    return buttons


def get_game_mode(screen):
    buttons = draw_menu(screen)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for rect, i in buttons:
                    if rect.collidepoint(event.pos):
                        return i