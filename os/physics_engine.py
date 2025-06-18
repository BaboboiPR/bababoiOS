import pygame
import sys

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
FPS = 60
GRAVITY = 0.5
FRICTION = 0.9
MIN_BOUNCE_VEL = 0.5
GROUND_FRICTION = 0.9

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Ball settings
BALL_RADIUS = 25
NUM_BALLS = 5
SPAWN_DELAY = 2000  # milliseconds (2 seconds)
last_spawn_time = pygame.time.get_ticks()


# Initialize multiple balls
balls = []
for i in range(NUM_BALLS):
    balls.append({
        "pos": [100 + i * 80, 100.0],
        "vel": [3.0 + i, 0.0],
        "color": BLUE,
        "bounces": 0
    })


def handle_collisions(ball):
    x, y = ball["pos"]
    vx, vy = ball["vel"]

    # Left/right walls
    if x - BALL_RADIUS <= 0 or x + BALL_RADIUS >= WIDTH:
        vx *= -FRICTION
        x = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, x))
        if abs(vx) < MIN_BOUNCE_VEL:
            vx = 0
        ball["bounces"] += 1
        print(f"Ball bounce: {ball['bounces']}")

    # Floor
    if y + BALL_RADIUS >= HEIGHT:
        if abs(vy) >= MIN_BOUNCE_VEL:
            vy *= -FRICTION
            ball["bounces"] += 1
            print(f"Ball bounce: {ball['bounces']}")
        else:
            vy = 0
        y = HEIGHT - BALL_RADIUS
        vx *= GROUND_FRICTION
        if abs(vx) < MIN_BOUNCE_VEL:
            vx = 0

    # Ceiling
    elif y - BALL_RADIUS <= 0:
        vy *= -FRICTION
        y = BALL_RADIUS
        if abs(vy) < MIN_BOUNCE_VEL:
            vy = 0
        ball["bounces"] += 1
        print(f"Ball bounce: {ball['bounces']}")
        vx *= GROUND_FRICTION
        if abs(vx) < MIN_BOUNCE_VEL:
            vx = 0

    ball["pos"] = [x, y]
    ball["vel"] = [vx, vy]


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill(WHITE)

    for ball in balls:
        # Apply gravity unless settled
        if not (ball["vel"][1] == 0 and ball["pos"][1] + BALL_RADIUS >= HEIGHT):
            ball["vel"][1] += GRAVITY

        # Update position
        ball["pos"][0] += ball["vel"][0]
        ball["pos"][1] += ball["vel"][1]

        # Handle collisions
        handle_collisions(ball)

        # Spawn new ball every SPAWN_DELAY ms
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= SPAWN_DELAY:
            balls.append({
                "pos": [100.0, 100.0],
                "vel": [3.0, 0.0],
                "color": BLUE,
                "bounces": 0
            })
            last_spawn_time = current_time

        # Draw
        pygame.draw.circle(screen, ball["color"], (int(ball["pos"][0]), int(ball["pos"][1])), BALL_RADIUS)

    pygame.display.flip()
    clock.tick(FPS)
