import pygame
import sys
import time

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
RED = (255, 0, 0)
FPS = 60
GRAVITY = 0.5
FRICTION = 0.9
MIN_BOUNCE_VEL = 0.5
GROUND_FRICTION = 0.9  # Friction when on the ground

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Ball properties
ball_pos = [100.0, 100.0]
ball_vel = [3.0, 0.0]
ball_radius = 25

bounces = 0

def handle_collisions():
    global bounces

    # Left/right walls
    if ball_pos[0] - ball_radius <= 0 or ball_pos[0] + ball_radius >= WIDTH:
        ball_vel[0] *= -FRICTION
        ball_pos[0] = max(ball_radius, min(WIDTH - ball_radius, ball_pos[0]))
        if abs(ball_vel[0]) < MIN_BOUNCE_VEL:
            ball_vel[0] = 0
        bounces += 1
        print("Bounce:", bounces)

    # Floor
    if ball_pos[1] + ball_radius >= HEIGHT:
        if abs(ball_vel[1]) >= MIN_BOUNCE_VEL:
            ball_vel[1] *= -FRICTION
            bounces += 1
            print("Bounce:", bounces)
        else:
            ball_vel[1] = 0  # Stop vertical movement

        ball_pos[1] = HEIGHT - ball_radius

        # Apply ground friction to horizontal movement
        ball_vel[0] *= GROUND_FRICTION
        if abs(ball_vel[0]) < MIN_BOUNCE_VEL:
            ball_vel[0] = 0

    # Ceiling
    elif ball_pos[1] - ball_radius <= 0:
        ball_vel[1] *= -FRICTION
        ball_pos[1] = ball_radius
        if abs(ball_vel[1]) < MIN_BOUNCE_VEL:
            ball_vel[1] = 0
        bounces += 1
        print("Bounce:", bounces)

        # Also slow horizontal motion if stuck up there
        ball_vel[0] *= GROUND_FRICTION
        if abs(ball_vel[0]) < MIN_BOUNCE_VEL:
            ball_vel[0] = 0

def making_balls():
    x = 50
    for i in range(5):
        i += 1
        pygame.draw.circle(screen, BLUE, (int(ball_pos[0] + (x * i)), int(ball_pos[1])), ball_radius)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Only apply gravity if not at rest on ground
    if not (ball_vel[1] == 0 and ball_pos[1] + ball_radius >= HEIGHT):
        ball_vel[1] += GRAVITY

    # Update position
    ball_pos[0] += ball_vel[0]
    ball_pos[1] += ball_vel[1]

    handle_collisions()

    # Drawing
    screen.fill(WHITE)
    making_balls()
    pygame.display.flip()
    clock.tick(FPS)
