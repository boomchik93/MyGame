import pygame
import random
import sqlite3
import time

pygame.init()

WIDTH, HEIGHT = 1280, 720

TEXT_COLOR = (0, 62, 151)
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Бег")
clock = pygame.time.Clock()

conn = sqlite3.connect("scores.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS scores (score INTEGER)")
conn.commit()

button_img = pygame.image.load("button.png").convert_alpha()
button_img = pygame.transform.scale(button_img, (250, 100))


def save_score(score):
    cursor.execute("INSERT INTO scores (score) VALUES (?)", (score,))
    conn.commit()


def get_top_scores():
    cursor.execute("SELECT score FROM scores ORDER BY score DESC LIMIT 5")
    return cursor.fetchall()


def load_image(name):
    image = pygame.image.load(name).convert_alpha()
    return image


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.sheet = load_image("player.png")
        self.frames = []
        self.cut_sheet(self.sheet, 8, 1)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT - 100)
        self.vel_y = 0
        self.base_speed = 2
        self.boosted_speed = 3
        self.vel_x = self.base_speed
        self.on_ground = False
        self.animation_timer = 0
        self.jump_height = 400
        self.jump_distance = 300
        self.start_y = self.rect.y
        self.jump_speed = -15
        self.gravity = 0.3

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows // 1.2)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = self.jump_speed
            self.on_ground = False

        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.top < self.start_y - self.jump_height:
            self.rect.top = self.start_y - self.jump_height
            self.vel_y = 0

        if self.rect.bottom >= HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.vel_y = 0
            self.on_ground = True

        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.animation_timer = 0

        if self.rect.y < self.start_y:
            self.vel_x = self.boosted_speed
        else:
            self.vel_x = self.base_speed


class Box(pygame.sprite.Sprite):
    def __init__(self, y_position, player):
        super().__init__()
        self.image = pygame.image.load("box.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (80, 80))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(WIDTH, WIDTH + 100)
        self.rect.y = y_position
        self.player = player
        self.scored = False

    def update(self):
        self.rect.x -= self.player.vel_x
        if self.rect.right < 0:
            self.kill()


class Bird(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.sheet = pygame.image.load("bird.png").convert_alpha()
        self.frames = []
        self.cut_sheet(self.sheet, 9, 1)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(WIDTH, WIDTH + 100)
        self.rect.y = random.randint(50, HEIGHT - 550)
        self.speed = player.base_speed * 3
        self.animation_timer = 0

    def cut_sheet(self, sheet, columns, rows):
        sheet_width, sheet_height = sheet.get_size()
        frame_width = sheet_width // columns
        frame_height = sheet_height // rows
        for j in range(rows):
            for i in range(columns):
                frame_location = (frame_width * i, frame_height * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, (frame_width, frame_height))))

    def update(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.animation_timer = 0

        self.rect.x -= self.speed

        if self.rect.right < 0:
            self.rect.x = random.randint(WIDTH, WIDTH + 100)
            self.rect.y = random.randint(50, HEIGHT - 550)


def show_high_scores():
    while True:
        screen.fill(SKY_BLUE)
        font = pygame.font.SysFont("Arial", 40)
        title = font.render("Топ 5 рекордов", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        scores = get_top_scores()
        y = 150
        for i, (score,) in enumerate(scores, 1):
            text = font.render(f"{i}. {score}", True, WHITE)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))
            y += 50
            if i >= 5:
                break

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return


def draw_button(surface, text, x, y):
    btn_rect = button_img.get_rect(center=(x, y))
    surface.blit(button_img, btn_rect)

    font = pygame.font.Font(None, 40)
    text_surf = font.render(text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=btn_rect.center)
    surface.blit(text_surf, text_rect)
    return btn_rect


def game_over_screen(state):
    screen.fill(SKY_BLUE)
    font = pygame.font.Font(None, 108)

    if state == "game_over":
        text = font.render(f"Счёт: {score}", True, TEXT_COLOR)
        buttons = ["Заново", "Рекорды", "Выход"]
    else:
        text = font.render("Пауза", True, TEXT_COLOR)
        buttons = ["Продолжить", "Рекорды", "Выход"]

    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 100))

    btn_rects = []
    y_pos = 250
    for btn_text in buttons:
        rect = draw_button(screen, btn_text, WIDTH // 2, y_pos)
        btn_rects.append((rect, btn_text))
        y_pos += 150

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for rect, text in btn_rects:
                    if rect.collidepoint(mouse_pos):
                        if text == "Заново" or text == "Продолжить":
                            return "game"
                        elif text == "Рекорды":
                            show_high_scores()
                            return game_over_screen(state)
                        elif text == "Выход":
                            return "quit"


def game_loop(fps, box_spawn_interval):
    global score
    while True:
        player = Player()
        all_sprites = pygame.sprite.Group()
        birds = pygame.sprite.Group()
        boxes = pygame.sprite.Group()
        all_sprites.add(player)

        font = pygame.font.SysFont("Arial", 108, italic=True)

        for _ in range(random.randint(1, 3)):
            bird = Bird(player)
            birds.add(bird)
            all_sprites.add(bird)

        score = 0
        last_box_spawn_time = time.time()
        background_image = pygame.image.load("background.png").convert()
        background_width = background_image.get_width()
        background_x = 0
        running_game = True

        while running_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        result = game_over_screen("pause")
                        if result == "quit":
                            return "quit"
                        elif result == "game":
                            continue

            if time.time() - last_box_spawn_time > box_spawn_interval:
                box = Box(player.rect.bottom - 80, player)
                boxes.add(box)
                all_sprites.add(box)
                last_box_spawn_time = time.time()

            all_sprites.update()

            background_x -= player.vel_x
            if background_x <= -background_width:
                background_x = 0

            screen.fill(WHITE)
            screen.blit(background_image, (background_x, 0))
            if background_x < 0:
                screen.blit(background_image, (background_x + background_width, 0))

            score_text = font.render(str(score), True, TEXT_COLOR)
            text_rect = score_text.get_rect(center=(WIDTH // 2, 100))
            screen.blit(score_text, text_rect)

            all_sprites.draw(screen)

            pygame.display.flip()
            clock.tick(fps)

            collision = False
            for box in boxes:
                if player.rect.colliderect(box.rect):
                    collision = True
                    break

            if collision:
                save_score(score)
                result = game_over_screen("game_over")
                if result == "game":
                    running_game = False
                else:
                    return "quit"

            if not collision:
                for box in boxes:
                    if not box.scored and box.rect.right < player.rect.left:
                        score += 50
                        box.scored = True

            if player.rect.bottom > HEIGHT:
                save_score(score)
                result = game_over_screen("game_over")
                if result == "game":
                    running_game = False
                else:
                    return "quit"


def main_menu():
    while True:
        screen.fill(SKY_BLUE)
        font = pygame.font.Font(None, 108)
        title = font.render("Бег", True, TEXT_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        btn_rects = []
        y_pos = 200
        for btn_text in ["Начальный", "Обычный", "Для опытных", "Рекорды", "Выход"]:
            rect = draw_button(screen, btn_text, WIDTH // 2, y_pos)
            btn_rects.append((rect, btn_text))
            y_pos += 100

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for rect, text in btn_rects:
                    if rect.collidepoint(mouse_pos):
                        if text == "Начальный":
                            result = game_loop(75, 7)
                            if result == "quit": return
                        elif text == "Обычный":
                            result = game_loop(120, 5)
                            if result == "quit": return
                        elif text == "Для опытных":
                            result = game_loop(240, 3)
                            if result == "quit": return
                        elif text == "Рекорды":
                            show_high_scores()
                        elif text == "Выход":
                            return


if __name__ == "__main__":
    main_menu()
    pygame.quit()
