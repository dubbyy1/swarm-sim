import pygame

class Checkbox:
    def __init__(self, x, y, text, get_checked, set_checked):
        self.x = x
        self.y = y
        self.size = 18
        self.text = text
        self.get_checked = get_checked
        self.set_checked = set_checked

    def draw(self, screen):
        rect = self.get_rect()
        pygame.draw.rect(screen, "#ffffff", rect)
        pygame.draw.rect(screen, "#000000", rect, 2)

        if self.get_checked():
            pygame.draw.line(
                screen,
                "#000000",
                (self.x + 4, self.y + 9),
                (self.x + 8, self.y + 14),
                2
            )
            pygame.draw.line(
                screen,
                "#000000",
                (self.x + 8, self.y + 14),
                (self.x + 15, self.y + 4),
                2
            )

        font = pygame.font.Font(None, 24)
        text = font.render(self.text, True, "#000000")
        screen.blit(text, (self.x + self.size + 8, self.y - 1))

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if not self.get_click_rect().collidepoint(event.pos):
            return False

        self.set_checked(not self.get_checked())
        return True

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def get_click_rect(self):
        return pygame.Rect(self.x, self.y - 2, 180, self.size + 4)


class Slider:
    def __init__(self, x, y, width, text, minimum, maximum, get_value, set_value, value_format="{:.0f}"):
        self.x = x
        self.y = y
        self.width = width
        self.text = text
        self.minimum = minimum
        self.maximum = maximum
        self.get_value = get_value
        self.set_value = set_value
        self.value_format = value_format
        self.dragging = False
        self.track_y = y + 26
        self.knob_radius = 7

    def draw(self, screen):
        font = pygame.font.Font(None, 24)
        value = self.get_value()
        label = font.render(f"{self.text}: {self.value_format.format(value)}", True, "#000000")
        screen.blit(label, (self.x, self.y))

        pygame.draw.line(
            screen,
            "#000000",
            (self.x, self.track_y),
            (self.x + self.width, self.track_y),
            2
        )

        knob_x = self.value_to_x(value)
        pygame.draw.circle(screen, "#ffffff", (int(knob_x), self.track_y), self.knob_radius)
        pygame.draw.circle(screen, "#000000", (int(knob_x), self.track_y), self.knob_radius, 2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.get_click_rect().collidepoint(event.pos):
                return False

            self.dragging = True
            self.set_value_from_mouse(event.pos[0])
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self.dragging
            self.dragging = False
            return was_dragging

        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_value_from_mouse(event.pos[0])
            return True

        return False

    def set_value_from_mouse(self, mouse_x):
        t = (mouse_x - self.x) / self.width
        t = max(0, min(1, t))
        self.set_value(self.minimum + t * (self.maximum - self.minimum))

    def value_to_x(self, value):
        t = (value - self.minimum) / (self.maximum - self.minimum)
        t = max(0, min(1, t))
        return self.x + t * self.width

    def get_click_rect(self):
        return pygame.Rect(
            self.x - self.knob_radius,
            self.y,
            self.width + self.knob_radius * 2,
            38
        )


class Stepper:
    def __init__(self, x, y, text, minimum, maximum, get_value, set_value):
        self.x = x
        self.y = y
        self.text = text
        self.minimum = minimum
        self.maximum = maximum
        self.get_value = get_value
        self.set_value = set_value
        self.button_size = 34
        self.label_width = 60

    def draw(self, screen):
        font = pygame.font.Font(None, 24)
        label = font.render(f"{self.text}: {self.get_value()}", True, "#000000")
        screen.blit(label, (self.x, self.y - 22))

        minus_rect = self.get_minus_rect()
        value_rect = self.get_value_rect()
        plus_rect = self.get_plus_rect()

        pygame.draw.rect(screen, "#ffffff", minus_rect)
        pygame.draw.rect(screen, "#ffffff", value_rect)
        pygame.draw.rect(screen, "#ffffff", plus_rect)
        pygame.draw.rect(screen, "#000000", minus_rect, 2)
        pygame.draw.rect(screen, "#000000", value_rect, 2)
        pygame.draw.rect(screen, "#000000", plus_rect, 2)

        minus = font.render("-", True, "#000000")
        value = font.render(str(self.get_value()), True, "#000000")
        plus = font.render("+", True, "#000000")

        screen.blit(minus, minus.get_rect(center=minus_rect.center))
        screen.blit(value, value.get_rect(center=value_rect.center))
        screen.blit(plus, plus.get_rect(center=plus_rect.center))

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        if self.get_minus_rect().collidepoint(event.pos):
            self.change_value(-1)
            return True

        if self.get_plus_rect().collidepoint(event.pos):
            self.change_value(1)
            return True

        return False

    def change_value(self, delta):
        value = self.get_value() + delta
        value = max(self.minimum, min(self.maximum, value))
        self.set_value(value)

    def get_minus_rect(self):
        return pygame.Rect(self.x, self.y, self.button_size + 2, self.button_size)

    def get_value_rect(self):
        return pygame.Rect(
            self.x + self.button_size,
            self.y,
            self.label_width,
            self.button_size
        )

    def get_plus_rect(self):
        return pygame.Rect(
            self.x + self.button_size + self.label_width - 2,
            self.y,
            self.button_size,
            self.button_size
        )


class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = (255, 255, 255)
        self.hover_color = (255, 255, 255)
        self.active_color = (40, 255, 80)
        self.callback = callback

    def draw(self, screen, active=False):
        mouse_position = pygame.mouse.get_pos()
        color = self.active_color if active else self.color
        if self.get_rect().collidepoint(mouse_position) and not active:
            color = self.hover_color

        pygame.draw.rect(screen, color, self.get_rect(), border_radius=6)
        pygame.draw.rect(screen, (30, 30, 30), self.get_rect(), 2, border_radius=6)

        font = pygame.font.Font(None, 28)
        text = font.render(self.text, True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text, text_rect)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if not self.get_rect().collidepoint(event.pos):
            return False

        self.callback()
        return True

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
