from swarm import World
from swarm.settings import Settings
from swarm.types import Formation, State
from ui import Button, Checkbox, Slider, Stepper

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
        agent.draw(screen, selected=agent == world.selected_agent)


def create_formation_buttons(world):
    return [
        (Formation.LINE, Button(
            12,
            12,
            100,
            34,
            "Line",
            lambda: world.controller.set_formation(Formation.LINE)
        )),
        (Formation.CIRCLE, Button(
            122,
            12,
            100,
            34,
            "Circle",
            lambda: world.controller.set_formation(Formation.CIRCLE)
        )),
        (Formation.IDLE, Button(
            232,
            12,
            100,
            34,
            "Idle",
            lambda: world.controller.set_formation(Formation.IDLE)
        )),
    ]


def create_remote_button(world):
    return Button(
        12,
        56,
        120,
        34,
        "Remote",
        world.toggle_remote_control
    )


def create_wall_buttons(world, screen):
    width, height = screen.get_size()
    button_width = 120
    button_height = 34
    x = width - button_width - 12

    return [
        ("wall", Button(
            x,
            height - 86,
            button_width,
            button_height,
            "Wall",
            world.toggle_wall_mode
        )),
        ("clear", Button(
            x,
            height - 46,
            button_width,
            button_height,
            "Clear walls",
            world.clear_walls
        )),
    ]


def create_reset_button(world, screen):
    _, height = screen.get_size()
    return Button(
        12,
        height - 46,
        100,
        34,
        "Reset",
        world.refresh
    )


def create_reset_steppers(world, screen):
    _, height = screen.get_size()
    return [
        Stepper(
            138,
            height - 46,
            "Swarm size",
            1,
            20,
            lambda: world.settings.reset_swarm_size,
            world.set_reset_swarm_size
        ),
        Stepper(
            138 + (134*1),
            height - 46,
            "Receivers",
            1,
            32,
            lambda: world.settings.reset_receiver_count,
            world.set_reset_receiver_count
        ),
        Stepper(
            138 + (134*2),
            height - 46,
            "Emitters",
            1,
            12,
            lambda: world.settings.reset_emitter_count,
            world.set_reset_emitter_count
        ),
    ]


def create_graphics_checkboxes(world):
    return [
        Checkbox(
            12,
            108,
            "Components",
            lambda: world.settings.show_components,
            lambda checked: setattr(world.settings, "show_components", checked)
        ),
        Checkbox(
            12,
            134,
            "Network lines",
            lambda: world.settings.show_network_lines,
            lambda checked: setattr(world.settings, "show_network_lines", checked)
        ),
        Checkbox(
            12,
            160,
            "Formation lines",
            lambda: world.settings.show_formation_lines,
            lambda checked: setattr(world.settings, "show_formation_lines", checked)
        ),
        Checkbox(
            12,
            186,
            "Wheel speeds",
            lambda: world.settings.show_wheel_speeds,
            lambda checked: setattr(world.settings, "show_wheel_speeds", checked)
        ),
        Checkbox(
            12,
            212,
            "Target positions",
            lambda: world.settings.show_target_positions,
            lambda checked: setattr(world.settings, "show_target_positions", checked)
        ),
        Checkbox(
            12,
            238,
            "IR range circle",
            lambda: world.settings.show_ir_range_circle,
            lambda checked: setattr(world.settings, "show_ir_range_circle", checked)
        ),
    ]


def create_ir_sliders(world):
    return [
        Slider(
            12,
            276,
            220,
            "IR max range",
            50,
            600,
            lambda: world.settings.ir_max_range,
            lambda value: setattr(world.settings, "ir_max_range", value),
            "{:.0f}px"
        ),
        Slider(
            12,
            326,
            220,
            "IR noise",
            0,
            0.5,
            lambda: world.settings.ir_noise,
            lambda value: setattr(world.settings, "ir_noise", value),
            "{:.2f}"
        ),
        Slider(
            12,
            376,
            220,
            "UWB noise",
            0,
            80,
            lambda: world.settings.uwb_distance_noise,
            lambda value: setattr(world.settings, "uwb_distance_noise", value),
            "{:.0f}px"
        ),
        Slider(
            12,
            426,
            220,
            "Wheel inaccuracy",
            0,
            0.5,
            lambda: world.settings.wheel_inaccuracy,
            lambda value: setattr(world.settings, "wheel_inaccuracy", value),
            "{:.0%}"
        ),
    ]


def draw_selected_robot_stats(world, screen, font):
    agent = world.selected_agent
    if agent is None:
        lines = ["Selected robot", "None"]
    else:
        vx, vy, omega = agent.drivetrain.velocity
        live_neighbours = agent.get_live_neighbours()
        lines = [
            "Selected robot",
            f"ID: {agent.id}",
            f"Pose: ({agent.pose.x:.1f}, {agent.pose.y:.1f}, {agent.pose.theta:.1f}°)",
            f"State: {agent.state.name}",
            f"Formation: {agent.formation.name}",
            f"Live neighbours: {live_neighbours}",
            f"Velocity: ({vx:.1f}, {vy:.1f})",
            f"Is leader: {agent.leader}",
        ]

    rendered_lines = [font.render(line, True, "#000000") for line in lines]
    width = max(line.get_width() for line in rendered_lines) + 20
    height = sum(line.get_height() for line in rendered_lines) + 16
    screen_width, _ = screen.get_size()
    x = screen_width - width - 12
    y = 12

    pygame.draw.rect(screen, "#ffffff", (x, y, width, height))
    pygame.draw.rect(screen, "#000000", (x, y, width, height), 2)

    text_y = y + 8
    for line in rendered_lines:
        screen.blit(line, (x + 10, text_y))
        text_y += line.get_height()


def draw_ui(world, screen, font, formation_buttons, remote_button, wall_buttons, reset_button, reset_steppers, graphics_checkboxes, ir_sliders):
    for formation, button in formation_buttons:
        button.draw(screen, active=world.controller.formation == formation)

    remote_button.draw(screen, active=world.settings.remote_control_enabled)
    for button_type, button in wall_buttons:
        button.draw(screen, active=button_type == "wall" and world.wall_mode_enabled)
    reset_button.draw(screen)
    for stepper in reset_steppers:
        stepper.draw(screen)

    for checkbox in graphics_checkboxes:
        checkbox.draw(screen)

    for slider in ir_sliders:
        slider.draw(screen)

    draw_selected_robot_stats(world, screen, font)

def main(screen, font, clock):
    settings = Settings()
    world = World(0, screen, settings)
    for i in range(6):
        world.spawn(1)
        world.tick(1)
    world.set_reset_swarm_size(len(world.agents))

    formation_buttons = create_formation_buttons(world)
    remote_button = create_remote_button(world)
    wall_buttons = create_wall_buttons(world, screen)
    reset_button = create_reset_button(world, screen)
    reset_steppers = create_reset_steppers(world, screen)
    graphics_checkboxes = create_graphics_checkboxes(world)
    ir_sliders = create_ir_sliders(world)
    running = True

    frames = 0
    while running:
        dt = clock.tick(60) / 1000  # seconds since last frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                handled = False

                for slider in ir_sliders:
                    if slider.handle_event(event):
                        handled = True

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for _, button in formation_buttons:
                        if button.handle_event(event):
                            handled = True
                            break

                    if not handled:
                        handled = remote_button.handle_event(event)

                    if not handled:
                        for _, button in wall_buttons:
                            if button.handle_event(event):
                                handled = True
                                break

                    if not handled:
                        handled = reset_button.handle_event(event)

                    if not handled:
                        for stepper in reset_steppers:
                            if stepper.handle_event(event):
                                handled = True
                                break

                    if not handled:
                        for checkbox in graphics_checkboxes:
                            if checkbox.handle_event(event):
                                handled = True
                                break

                    if not handled:
                        if world.wall_mode_enabled:
                            world.handle_wall_click(event.pos)
                        else:
                            world.select_agent_at(event.pos)

        keys = pygame.key.get_pressed()
        remote_x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        remote_y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])

        if (
            world.settings.remote_control_enabled
            and world.selected_agent is not None
            and world.selected_agent.state == State.REMOTE
        ):
            world.selected_agent.set_remote_input(remote_x, remote_y)

        screen.fill("#ffffff")
        world.tick(dt)

        draw_elements(world, screen)
        draw_ui(world, screen, font, formation_buttons, remote_button, wall_buttons, reset_button, reset_steppers, graphics_checkboxes, ir_sliders)

        pygame.display.flip()

        frames += 1

if __name__ == "__main__":
    screen, font, clock = start()
    main(screen, font, clock)
