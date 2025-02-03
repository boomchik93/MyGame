import pygame
import random
import sqlite3
import time

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720

TEXT_COLOR = (0, 62, 151)
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("БоксДжампер")
clock = pygame.time.Clock()

pygame.mixer.music.load("music.mp3")
pygame.mixer.music.play(-1)

conn = sqlite3.connect("scores.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS scores_beginner (score INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS scores_normal (score INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS scores_expert (score INTEGER)")
conn.commit()

button_img = pygame.image.load("button.png").convert_alpha()
button_img = pygame.transform.scale(button_img, (250, 100))



def save_score(score, level):
    table_name = f"scores_{level}"
    cursor.execute(f"INSERT INTO {table_name} (score) VALUES (?)", (score,))
    conn.commit()


def get_top_scores(level):
    table_name = f"scores_{level}"
    cursor.execute(f"SELECT score FROM {table_name} ORDER BY score DESC LIMIT 5")
    return cursor.fetchall()


def load_image(name):
    return pygame.image.load(name).convert_alpha()


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
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows // 1.2)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

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
    def __init__(self, y_position, player, level):
        super().__init__()
        self.image = pygame.image.load("box.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (80, 80))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(WIDTH, WIDTH + 100)
        self.rect.y = y_position
        self.player = player
        self.scored = False
        self.level = level

        if self.level == "expert":
            self.image = pygame.Surface((80, 160), pygame.SRCALPHA)
            box1 = pygame.image.load("box.png").convert_alpha()
            box1 = pygame.transform.scale(box1, (80, 80))
            box2 = pygame.transform.scale(box1, (80, 80))
            self.image.blit(box1, (0, 0))
            self.image.blit(box2, (0, 80))
            self.rect = self.image.get_rect(topleft=(self.rect.x, y_position - 80))

    def update(self):
        self.rect.x -= self.player.vel_x
        if self.rect.right < 0:
            self.kill()


class Bird(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.sheet = load_image("bird.png").convert_alpha()
        self.frames = []
        self.cut_sheet(self.sheet, 9, 1)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(WIDTH, WIDTH + 100)
        self.rect.y = random.randint(50, HEIGHT - 600)
        self.speed = player.base_speed * 3
        self.animation_timer = 0

    def cut_sheet(self, sheet, columns, rows):
        frame_width = sheet.get_width() // columns
        frame_height = sheet.get_height() // rows
        for j in range(rows):
            for i in range(columns):
                frame_location = (frame_width * i, frame_height * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, (frame_width, frame_height))))

    def update(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.animation_timer = 0

        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.rect.x = random.randint(WIDTH, WIDTH + 100)
            self.rect.y = random.randint(50, HEIGHT - 600)


def show_high_scores():
    background_image = pygame.image.load("background.png").convert()
    level_data = [
        ('beginner', 'Начальный', (TEXT_COLOR, WIDTH // 6)),
        ('normal', 'Обычный', (TEXT_COLOR, WIDTH // 2)),
        ('expert', 'Эксперт', (TEXT_COLOR, WIDTH - WIDTH // 6))
    ]

    while True:
        screen.blit(background_image, (0, 0))

        pygame.draw.line(screen, TEXT_COLOR, (WIDTH // 3, 100), (WIDTH // 3, HEIGHT - 50), 2)
        pygame.draw.line(screen, TEXT_COLOR, (WIDTH * 2 // 3, 100), (WIDTH * 2 // 3, HEIGHT - 50), 2)

        font_title = pygame.font.SysFont("Arial", 50, bold=True)
        font_scores = pygame.font.SysFont("Arial", 40)

        title = font_title.render("Топ 5 рекордов", True, TEXT_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        for level, name, (color, x_pos) in level_data:
            level_title = font_title.render(name, True, color)
            screen.blit(level_title, (x_pos - level_title.get_width() // 2, 100))

            y = 160
            scores = get_top_scores(level)

            if not scores:
                no_scores = font_scores.render("Нет результатов", True, color)
                screen.blit(no_scores, (x_pos - no_scores.get_width() // 2, y))
            else:
                for i, (score,) in enumerate(scores, 1):
                    text = font_scores.render(f"{i}. {score}", True, color)
                    screen.blit(text, (x_pos - text.get_width() // 2, y))
                    y += 45

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return


def draw_button(surface, text, x, y):
    btn_rect = button_img.get_rect(center=(x, y))
    surface.blit(button_img, btn_rect)
    font = pygame.font.Font(None, 40)
    text_surf = font.render(text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=btn_rect.center)
    surface.blit(text_surf, text_rect)
    return btn_rect


def game_over_screen(state, level):
    background_image = pygame.image.load("background.png").convert()
    while True:
        screen.blit(background_image, (0, 0))
        font = pygame.font.Font(None, 108)

        if state == "game_over":
            text = font.render(f"Счёт: {score}", True, TEXT_COLOR)
            buttons = ["Заново", "Рекорды", "В меню"]
        else:
            text = font.render("Пауза", True, TEXT_COLOR)
            buttons = ["Продолжить", "Рекорды", "В меню"]

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
                            if text == "Заново":
                                return "restart"
                            elif text == "Продолжить":
                                return "continue"
                            elif text == "Рекорды":
                                show_high_scores()
                                return game_over_screen(state, level)
                            elif text == "В меню":
                                return "menu"


def game_loop(fps, box_spawn_interval, level):
    global score
    while True:
        player = Player()
        all_sprites = pygame.sprite.Group()
        birds = pygame.sprite.Group()
        boxes = pygame.sprite.Group()
        all_sprites.add(player)

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
        start_time = time.time()
        font = pygame.font.SysFont("Arial", 36)

        while running_game:
            current_time = int(time.time() - start_time)
            time_text = font.render(f"Время: {current_time}", True, TEXT_COLOR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    result = game_over_screen("pause", level)
                    if result == "continue":
                        continue
                    elif result == "restart":
                        running_game = False
                    elif result == "menu":
                        return "menu"
                    else:
                        return "quit"

            if time.time() - last_box_spawn_time > box_spawn_interval:
                y_position = HEIGHT - 130 if level != "expert" else HEIGHT - 130
                box = Box(y_position, player, level)
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

            score_text = font.render(f"Счёт: {score}", True, TEXT_COLOR)
            screen.blit(score_text, (20, 20))
            screen.blit(time_text, (WIDTH - time_text.get_width() - 20, 20))

            all_sprites.draw(screen)
            pygame.display.flip()
            clock.tick(fps)

            if pygame.sprite.spritecollideany(player, boxes) or player.rect.bottom > HEIGHT:
                save_score(score, level)
                result = game_over_screen("game_over", level)
                if result == "restart":
                    running_game = False
                elif result == "menu":
                    return "menu"
                else:
                    return "quit"

            for box in boxes:
                if not box.scored and box.rect.right < player.rect.left:
                    score += 50
                    box.scored = True


def main_menu():
    background_image = pygame.image.load("background.png").convert()
    while True:
        screen.blit(background_image, (0, 0))
        font = pygame.font.Font(None, 108)
        title = font.render("БоксДжампер", True, TEXT_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        btn_rects = []
        y_pos = 200
        for btn_text in ["Начальный", "Обычный", "Эксперт", "Рекорды", "Выход"]:
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
                            result = game_loop(75, 7, 'beginner')
                            if result == "menu":
                                continue
                            else:
                                return
                        elif text == "Обычный":
                            result = game_loop(120, 5, 'normal')
                            if result == "menu":
                                continue
                            else:
                                return
                        elif text == "Эксперт":
                            result = game_loop(240, 3, 'expert')
                            if result == "menu":
                                continue
                            else:
                                return
                        elif text == "Рекорды":
                            show_high_scores()
                        elif text == "Выход":
                            return


if __name__ == "__main__":
    main_menu()
    pygame.quit()
    conn.close()