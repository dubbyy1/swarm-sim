from swarm import World
from swarm.types import Formation

import pygame

def start():
    pygame.init()
    font = pygame.font.Font(None, 24)

    screen = pygame.display.set_mode((900, 600))
    pygame.display.set_caption("swarm")

    clock = pygame.time.Clock()

    return screen, font, clock

def draw_elements(world, screen):
    world.draw(screen)

    for agent in world.agents:
        agent.draw(screen)

def main(screen, font, clock):
    world = World(0, screen)
    for i in range(5):
        world.spawn(1)
        world.tick(1)

    running = True

    frames = 0
    while running:
        dt = clock.tick(60) / 1000  # seconds since last frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill("#ffffff")
        world.tick(dt)

        draw_elements(world, screen)

        pygame.display.flip()

        frames += 1
        if frames % 600 == 0:
            if frames % 1200 == 0:
                world.controller.set_formation(Formation.LINE)
            else:
                world.controller.set_formation(Formation.CIRCLE)

if __name__ == "__main__":
    screen, font, clock = start()
    main(screen, font, clock)
