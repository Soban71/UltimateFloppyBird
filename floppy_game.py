# floppy_game_advanced.py
import pygame
import random
import sys
import math  # ✅ Added for rotation

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game Constants
WIDTH = 800
HEIGHT = 700
FPS = 60
GRAVITY = 0.35
FLAP_STRENGTH = -8
PIPE_GAP = 200
PIPE_WIDTH = 80
BIRD_WIDTH = 45
BIRD_HEIGHT = 35
LEVEL_UP_SCORE = 10

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)

BACKGROUND_COLORS = [(135, 206, 235), (250, 214, 165), (255, 160, 122), (25, 25, 112)]
BACKGROUND_NAMES = ["Morning", "Noon", "Sunset", "Night"]

# Load sounds
flap_sound = pygame.mixer.Sound("sounds/flap.wav")
hit_sound = pygame.mixer.Sound("sounds/hit.wav")
point_sound = pygame.mixer.Sound("sounds/point.wav")
powerup_sound = pygame.mixer.Sound("sounds/powerup.wav")

# Load bird skins
bird_skins = [
    pygame.transform.scale(pygame.image.load("skins/default.png"), (BIRD_WIDTH, BIRD_HEIGHT)),
    pygame.transform.scale(pygame.image.load("skins/ninja.png"), (BIRD_WIDTH, BIRD_HEIGHT)),
    pygame.transform.scale(pygame.image.load("skins/rainbow.png"), (BIRD_WIDTH, BIRD_HEIGHT)),
    pygame.transform.scale(pygame.image.load("skins/robot.png"), (BIRD_WIDTH, BIRD_HEIGHT)),
]

# Screen Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Floppy Bird Advanced")
clock = pygame.time.Clock()

# Global flags
sound_enabled = True
paused = False

# Bird Class
class Bird:
    def __init__(self):
        self.x = 100
        self.y = HEIGHT // 2
        self.velocity = 0
        self.skin_index = 0
        self.rect = pygame.Rect(self.x, self.y, BIRD_WIDTH, BIRD_HEIGHT)
        self.shield = False
        self.angle = 0

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.angle = max(-30, min(30, -self.velocity * 3))  # Rotation angle
        self.rect.y = int(self.y)

    def flap(self):
        self.velocity = FLAP_STRENGTH
        if sound_enabled:
            flap_sound.play()

    def draw(self):
        skin = bird_skins[self.skin_index]
        rotated_skin = pygame.transform.rotate(skin, self.angle)
        rotated_rect = rotated_skin.get_rect(center=(self.x + BIRD_WIDTH // 2, self.y + BIRD_HEIGHT // 2))
        screen.blit(rotated_skin, rotated_rect.topleft)
        if self.shield:
            pygame.draw.circle(screen, (173, 216, 230), (self.x + 22, self.y + 18), 30, 3)

# Pipe Class
class Pipe:
    def __init__(self, x, gap):
        self.x = x
        self.height = random.randint(100, 400)
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + gap, PIPE_WIDTH, HEIGHT - self.height - gap)
        self.rotating = random.choice([True, False])  # Some pipes rotate
        self.angle = 0

    def update(self):
        self.x -= 3
        if self.rotating:
            self.angle = (self.angle + 2) % 360
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.top_rect)
        pygame.draw.rect(screen, GREEN, self.bottom_rect)

# Power-Up Class
class PowerUp:
    def __init__(self, x, y, type):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.type = type

    def draw(self):
        color = (255, 0, 0) if self.type == "slow" else (0, 0, 255) if self.type == "shield" else (255, 215, 0)
        pygame.draw.ellipse(screen, color, self.rect)

# Game Logic
def check_collision(bird, pipes):
    for pipe in pipes:
        if bird.rect.colliderect(pipe.top_rect) or bird.rect.colliderect(pipe.bottom_rect):
            if bird.shield:
                bird.shield = False
                if sound_enabled:
                    powerup_sound.play()
                return False
            else:
                if sound_enabled:
                    hit_sound.play()
                return True
    if bird.y < 0 or bird.y > HEIGHT:
        if sound_enabled:
            hit_sound.play()
        return True
    return False

def main():
    global sound_enabled, paused

    bird = Bird()
    pipes = []
    powerups = []
    score = 0
    level = 1
    frame = 0
    font = pygame.font.SysFont(None, 40)
    background_index = 0
    slow_motion_timer = 0
    double_points_timer = 0
    game_speed = 1
    global invincible_time
    invincible_time = pygame.time.get_ticks()

    running = True
    while running:
        clock.tick(FPS if slow_motion_timer <= 0 else FPS // 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()
                elif event.key == pygame.K_m:
                    sound_enabled = not sound_enabled
                elif event.key == pygame.K_p:
                    paused = not paused

        if paused:
            pause_text = font.render("Game Paused. Press [P] to Resume", True, (255, 255, 0))
            screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))
            pygame.display.update()
            continue

        screen.fill(BACKGROUND_COLORS[background_index])

        # Update game logic
        bird.update()

        if frame % int(90 / game_speed) == 0:
            current_gap = max(120, 200 - score * 2)
            pipes.append(Pipe(WIDTH, current_gap))
        if frame % 300 == 0:
            p_type = random.choice(["slow", "shield", "double"])
            powerups.append(PowerUp(WIDTH, random.randint(100, 400), p_type))

        for pipe in pipes:
            pipe.update()
        pipes = [pipe for pipe in pipes if pipe.x > -PIPE_WIDTH]

        for pu in powerups:
            pu.rect.x -= 3
        powerups = [pu for pu in powerups if pu.rect.x > -30]

        # Check collisions
        if pygame.time.get_ticks() - invincible_time > 2000:
            if check_collision(bird, pipes):
                game_over_screen(score)
                return

        # Power-up pickup
        for pu in powerups:
            if bird.rect.colliderect(pu.rect):
                if pu.type == "slow":
                    slow_motion_timer = FPS * 3
                elif pu.type == "shield":
                    bird.shield = True
                elif pu.type == "double":
                    double_points_timer = FPS * 3
                if sound_enabled:
                    powerup_sound.play()
                powerups.remove(pu)

        # Scoring
        for pipe in pipes:
            if pipe.x + PIPE_WIDTH == bird.x:
                if sound_enabled:
                    point_sound.play()
                score += 2 if double_points_timer > 0 else 1
                if score % LEVEL_UP_SCORE == 0:
                    level += 1
                    background_index = (background_index + 1) % len(BACKGROUND_COLORS)
                    bird.skin_index = min(len(bird_skins) - 1, bird.skin_index + 1)

        # Draw everything
        bird.draw()
        for pipe in pipes:
            pipe.draw()
        for pu in powerups:
            pu.draw()

        # HUD
        score_text = font.render(f"Score: {score}  Level: {level} ({BACKGROUND_NAMES[background_index]})", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Power-up status
        if slow_motion_timer > 0:
            screen.blit(font.render("Slow Motion", True, (255, 0, 0)), (10, 50))
        if double_points_timer > 0:
            screen.blit(font.render("Double Points", True, (255, 215, 0)), (10, 80))
        if bird.shield:
            screen.blit(font.render("Shield ON", True, (173, 216, 230)), (10, 110))

        pygame.display.update()
        frame += 1
        slow_motion_timer -= 1
        double_points_timer -= 1

def game_over_screen(score):
    font = pygame.font.SysFont("comicsansms", 60, bold=True)
    small_font = pygame.font.SysFont("comicsansms", 36)

    while True:
        screen.fill((135, 206, 235))
        text = font.render("GAME OVER!", True, (255, 69, 0))
        score_text = small_font.render(f"Your Score: {score}", True, (0, 0, 0))
        restart_text = small_font.render("Press [R] to Restart  |  Press [E] to Exit", True, (0, 0, 128))

        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 120))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                    return
                if event.key == pygame.K_e:
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    main()
