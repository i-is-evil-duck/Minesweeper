import pygame
import random
import sys
import time

# ----------------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------------
GRID_SIZE = 740
HUD_HEIGHT = 60
WIDTH, HEIGHT = 740, GRID_SIZE + HUD_HEIGHT

ROWS, COLS = 10, 10
CELL_SIZE = GRID_SIZE // COLS
BOMB_COUNT = 15

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minesweeper")

FONT = pygame.font.SysFont("arial", 32)

# Colors
BG = (50, 50, 50)
TILE_HIDDEN = (150, 150, 150)
TILE_REVEALED = (220, 220, 220)
TILE_BORDER = (100, 100, 100)
BOMB_COLOR = (200, 0, 0)
FLAG_COLOR = (255, 220, 0)
HUD_BG = (40, 40, 40)
HUD_TEXT = (240, 240, 240)
BUTTON_BG = (100, 100, 200)
BUTTON_TEXT = (255, 255, 255)

NUM_COLORS = {
    1: (20, 20, 255),
    2: (0, 150, 0),
    3: (255, 0, 0),
    4: (0, 0, 120),
    5: (120, 0, 0),
    6: (0, 120, 120),
    7: (0, 0, 0),
    8: (100, 100, 100),
}

# ----------------------------------------------------------------
# BOARD GENERATION
# ----------------------------------------------------------------
def generate_board():
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    bombs = set()

    while len(bombs) < BOMB_COUNT:
        r = random.randrange(ROWS)
        c = random.randrange(COLS)
        bombs.add((r, c))

    for (r, c) in bombs:
        board[r][c] = -1

    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == -1:
                continue
            count = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if board[nr][nc] == -1:
                            count += 1
            board[r][c] = count
    return board, bombs

def restart_game():
    global board, bombs, revealed, flags, game_over
    board, bombs = generate_board()
    revealed = [[False] * COLS for _ in range(ROWS)]
    flags = [[False] * COLS for _ in range(ROWS)]
    game_over = False

board, bombs = generate_board()
revealed = [[False] * COLS for _ in range(ROWS)]
flags = [[False] * COLS for _ in range(ROWS)]
game_over = False
auto_play = False  # Auto-play flag

# ----------------------------------------------------------------
# FLOOD REVEAL
# ----------------------------------------------------------------
def reveal(r, c):
    if revealed[r][c] or flags[r][c]:
        return
    revealed[r][c] = True
    if board[r][c] == 0:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    if not revealed[nr][nc]:
                        reveal(nr, nc)

# ----------------------------------------------------------------
# WIN CHECK
# ----------------------------------------------------------------
def check_win():
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != -1 and not revealed[r][c]:
                return False
    return True

# ----------------------------------------------------------------
# DRAWING
# ----------------------------------------------------------------
def draw_hud():
    pygame.draw.rect(screen, HUD_BG, (0, 0, WIDTH, HUD_HEIGHT))
    flags_used = sum(sum(row) for row in flags)
    mines_left = BOMB_COUNT - flags_used
    text = FONT.render(f"Mines Left: {mines_left}", True, HUD_TEXT)
    screen.blit(text, (20, 10))
    # Solve Step button
    pygame.draw.rect(screen, BUTTON_BG, (WIDTH - 360, 10, 170, 40))
    screen.blit(FONT.render("Solve Step", True, BUTTON_TEXT), (WIDTH - 350, 15))
    # Auto Play button
    pygame.draw.rect(screen, BUTTON_BG, (WIDTH - 180, 10, 160, 40))
    auto_text = "Auto: ON" if auto_play else "Auto: OFF"
    screen.blit(FONT.render(auto_text, True, BUTTON_TEXT), (WIDTH - 170, 15))

def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            x = c * CELL_SIZE
            y = HUD_HEIGHT + r * CELL_SIZE
            if revealed[r][c]:
                pygame.draw.rect(screen, TILE_REVEALED, (x, y, CELL_SIZE, CELL_SIZE))
                if board[r][c] > 0:
                    color = NUM_COLORS.get(board[r][c], (0, 0, 0))
                    screen.blit(FONT.render(str(board[r][c]), True, color), (x + CELL_SIZE // 3, y + CELL_SIZE // 5))
                if board[r][c] == -1:
                    pygame.draw.circle(screen, BOMB_COLOR, (x + CELL_SIZE // 2, y + CELL_SIZE // 2), CELL_SIZE // 4)
            else:
                pygame.draw.rect(screen, TILE_HIDDEN, (x, y, CELL_SIZE, CELL_SIZE))
                if flags[r][c]:
                    flag_font = pygame.font.SysFont("segoeuiemoji", CELL_SIZE - 30)
                    screen.blit(flag_font.render("🚩", True, (255, 0, 0)), (x + CELL_SIZE // 8, y + CELL_SIZE // 8))
            pygame.draw.rect(screen, TILE_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 1)

def draw():
    screen.fill(BG)
    draw_hud()
    draw_grid()
    pygame.display.flip()

# ----------------------------------------------------------------
# SOLVER LOGIC
# ----------------------------------------------------------------
def get_neighbors(r, c):
    neighbors = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nr, nc = r + dr, c + dc
            if (dr != 0 or dc != 0) and 0 <= nr < ROWS and 0 <= nc < COLS:
                neighbors.append((nr, nc))
    return neighbors

def solver_step(allow_guess=True):
    moved = False
    for r in range(ROWS):
        for c in range(COLS):
            if revealed[r][c] and board[r][c] > 0:
                neighbors = get_neighbors(r, c)
                hidden = [(nr, nc) for (nr, nc) in neighbors if not revealed[nr][nc] and not flags[nr][nc]]
                flagged = [(nr, nc) for (nr, nc) in neighbors if flags[nr][nc]]
                if len(hidden) > 0 and len(hidden) + len(flagged) == board[r][c]:
                    for (nr, nc) in hidden:
                        flags[nr][nc] = True
                        moved = True
                if len(flagged) == board[r][c]:
                    for (nr, nc) in hidden:
                        reveal(nr, nc)
                        moved = True

    # If no safe moves and guessing is allowed
    if not moved and allow_guess:
        hidden_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if not revealed[r][c] and not flags[r][c]]
        if hidden_cells:
            r, c = random.choice(hidden_cells)
            if board[r][c] == -1:
                for (br, bc) in bombs:
                    revealed[br][bc] = True
                global game_over
                game_over = True
                pygame.display.set_caption("BOOM! Restarting...")
                pygame.display.flip()
                time.sleep(1.2)
                restart_game()
            else:
                reveal(r, c)
                moved = True

    return moved

def auto_solver():
    global game_over
    moved = solver_step()
    if not moved:
        hidden_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if not revealed[r][c] and not flags[r][c]]
        if hidden_cells:
            r, c = random.choice(hidden_cells)
            if board[r][c] == -1:
                for (br, bc) in bombs:
                    revealed[br][bc] = True
                game_over = True
                pygame.display.set_caption("BOOM! Restarting...")
                pygame.display.flip()
                time.sleep(1.2)
                restart_game()
            else:
                reveal(r, c)

# ----------------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------------
running = True
while running:
    draw()
    if not game_over and check_win():
        pygame.display.set_caption("You win! Restarting...")
        pygame.display.flip()
        time.sleep(1.2)
        restart_game()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if my < HUD_HEIGHT:
                # Solve Step button
                if WIDTH - 360 <= mx <= WIDTH - 200 and 10 <= my <= 50:
                    if not game_over:
                        solver_step()
                # Auto Play button
                if WIDTH - 180 <= mx <= WIDTH - 20 and 10 <= my <= 50:
                    auto_play = not auto_play
                continue

            r = (my - HUD_HEIGHT) // CELL_SIZE
            c = mx // CELL_SIZE
            if not game_over:
                if event.button == 1 and not flags[r][c]:
                    if board[r][c] == -1:
                        for (br, bc) in bombs:
                            revealed[br][bc] = True
                        game_over = True
                        pygame.display.set_caption("BOOM! Restarting...")
                        pygame.display.flip()
                        time.sleep(1.2)
                        restart_game()
                    else:
                        reveal(r, c)
                if event.button == 3 and not revealed[r][c]:
                    flags[r][c] = not flags[r][c]

    if auto_play and not game_over:
        auto_solver()
        pygame.time.wait(100)  # visible speed for auto play

pygame.quit()
sys.exit()
