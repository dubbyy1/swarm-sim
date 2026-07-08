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
    for i in range(6):
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
        if frames == 180:
            world.controller.set_formation(Formation.LINE)

if __name__ == "__main__":
    screen, font, clock = start()
    main(screen, font, clock)

# pygame.init()
# font = pygame.font.Font(None, 24)


# running = True

# world = World(5, 900, 600, 20)
# world.set_formation(Formation.LINE)

# def refresh():
#     world.refresh()
#     world.set_formation(Formation.LINE)

# buttons = [
#     ui.Button(10, 10, 100, 50, "Refresh", refresh)
# ]


# while running:
#     dt = clock.tick(1) / 1000  # seconds since last frame
#     world.tick(dt)

#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         if event.type == pygame.MOUSEBUTTONDOWN:
#             for button in buttons:
#                 if button.get_rect().collidepoint(event.pos):
#                     button.callback()

#     screen.fill("#ffffff")
#     for button in buttons:
#         button.draw(screen)

#     for agent in world.agents:
#         pygame.draw.circle(screen, "#000000", agent.get_pos(), radius, 2)

#         for receiver in agent.get_receivers():
#             receiver_x, receiver_y, _ = receiver.get_pose()
#             pygame.draw.circle(screen, "#0066ff", (receiver_x, receiver_y), 2)

#         for emitter in agent.get_emitters():
#             emitter_x, emitter_y, _ = emitter.get_pose()
#             pygame.draw.circle(screen, "#ff3333", (emitter_x, emitter_y), 2)

#         id_label = font.render(agent.text, True, "#000000")
#         screen.blit(id_label, agent.get_text_pos())

#     pygame.display.flip()

# pygame.quit()
