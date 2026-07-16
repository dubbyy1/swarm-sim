import math
import random
import pygame

from .utils import Pose

class IRReceiver:
    def __init__(self, agent, network, id):
        self.id = id
        self.agent = agent
        self.network = network

        self.pose = Pose(0, 0, 0)

    def set_pose(self, pose):
        self.pose = pose
    def get_pose(self):
        return self.pose
    def get_global_pose(self):
        heading = math.radians(self.agent.pose.theta)
        x = self.agent.pose.x + self.pose.x * math.cos(heading) - self.pose.y * math.sin(heading)
        y = self.agent.pose.y + self.pose.x * math.sin(heading) + self.pose.y * math.cos(heading)
        theta = (self.agent.pose.theta + self.pose.theta) % 360
        return Pose(x, y, theta)

    def receive(self, packet, signal_strength):
        self.agent.receive_ir(self.id, packet, signal_strength)

    def draw(self, screen):
        global_pose = self.get_global_pose()
        pygame.draw.circle(screen, (0, 0, 255), (global_pose.x, global_pose.y), 2.5)

class IREmitter:
    def __init__(self, agent, network, id):
        self.id = id
        self.agent = agent
        self.network = network

        self.cone_width = 120
        self.pose = Pose(0, 0, 0)

    def crc8(self, data: bytes) -> int:
        crc = 0x00
        polynomial = 0x07

        for byte in data:
            crc ^= byte

            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ polynomial) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF

        return crc

    def emit(self, packet):
        packet.append(self.id)
        packet.append(self.crc8(bytes(packet)))

        sender_pose = self.get_global_pose()
        self.network.broadcast_ir(
            sender_pose=sender_pose,
            packet=packet,
            cone_width=self.cone_width,
            sglobal=sender_pose
        )

    def set_pose(self, pose):
        self.pose = pose
    def get_pose(self):
        return self.pose
    def get_global_pose(self):
        heading = math.radians(self.agent.pose.theta)
        x = self.agent.pose.x + self.pose.x * math.cos(heading) - self.pose.y * math.sin(heading)
        y = self.agent.pose.y + self.pose.x * math.sin(heading) + self.pose.y * math.cos(heading)
        theta = (self.agent.pose.theta + self.pose.theta) % 360
        return Pose(x, y, theta)

    def draw_cone(self, screen):
        global_pose = self.get_global_pose()
        theta = math.radians(global_pose.theta)
        half_cone = math.radians(self.cone_width / 2)
        cone_length = self.agent.settings.ir_max_range
        cone_points = [
            (global_pose.x, global_pose.y),
            (
                global_pose.x + cone_length * math.cos(theta + half_cone),
                global_pose.y + cone_length * math.sin(theta + half_cone),
            ),
            (
                global_pose.x + cone_length * math.cos(theta - half_cone),
                global_pose.y + cone_length * math.sin(theta - half_cone),
            ),
        ]

        cone_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surface, (255, 0, 0, 35), cone_points)
        screen.blit(cone_surface, (0, 0))

    def draw(self, screen):
        global_pose = self.get_global_pose()
        pygame.draw.circle(screen, (255, 0, 0), (global_pose.x, global_pose.y), 2.5)

class UWBAntenna:
    def __init__(self, agent, network):
        self.agent = agent
        self.network = network
        self.pose = Pose(0, 0, 0)

    def set_pose(self, pose):
        self.pose = pose
    def get_pose(self):
        return self.pose
    def get_global_pose(self):
        heading = math.radians(self.agent.pose.theta)
        x = self.agent.pose.x + self.pose.x * math.cos(heading) - self.pose.y * math.sin(heading)
        y = self.agent.pose.y + self.pose.x * math.sin(heading) + self.pose.y * math.cos(heading)
        theta = (self.agent.pose.theta + self.pose.theta) % 360
        return Pose(x, y, theta)

    def transmit(self, packet):
        self.network.broadcast_uwb(self.get_global_pose(), packet)

    def receive(self, packet, distance):
        self.agent.receive_uwb(packet, distance)

    # def draw(self, screen):
    #     global_pose = self.get_global_pose()
    #     pygame.draw.circle(screen, (0, 255, 0), (global_pose.x, global_pose.y), 2.5)

class Radio:
    def __init__(self, agent, network):
        self.agent = agent
        self.network = network
        self.pose = Pose(0, 0, 0)

    def set_pose(self, pose):
        self.pose = pose
    def get_pose(self):
        return self.pose
    def get_global_pose(self):
        heading = math.radians(self.agent.pose.theta)
        x = self.agent.pose.x + self.pose.x * math.cos(heading) - self.pose.y * math.sin(heading)
        y = self.agent.pose.y + self.pose.x * math.sin(heading) + self.pose.y * math.cos(heading)
        theta = (self.agent.pose.theta + self.pose.theta) % 360
        return Pose(x, y, theta)

    def transmit(self, packet):
        self.network.broadcast_radio(packet)

    def broadcast(self, packet):
        self.transmit(packet)

    def receive(self, packet):
        self.agent.receive_radio(packet)

    # def draw(self, screen):
    #     global_pose = self.get_global_pose()
    #     pygame.draw.circle(screen, (255, 165, 0), (global_pose.x, global_pose.y), 2.5)


class Drivetrain:
    def __init__(self, agent, settings):
        self.agent = agent
        self.settings = settings
        self.wheel_angles = [0, 120, 240]
        self.base_radius = agent.radius + 2
        self.wheel_diameter = 24
        self.wheel_width = 2
        self.max_wheel_speed = agent.speed * 2.5
        self.max_wheel_acceleration = agent.speed * 8
        self.target_wheel_speeds = [0.0, 0.0, 0.0]
        self.wheel_speeds = [0.0, 0.0, 0.0]
        self.wheel_error_profile = [random.uniform(-1, 1) for _ in self.wheel_angles]
        self.velocity = [0.0, 0.0, 0.0]

    def clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def world_to_body(self, vx, vy):
        heading = math.radians(self.agent.pose.theta)
        cos_heading = math.cos(heading)
        sin_heading = math.sin(heading)

        return [
            vx * cos_heading + vy * sin_heading,
            -vx * sin_heading + vy * cos_heading
        ]

    def body_to_world(self, vx, vy):
        heading = math.radians(self.agent.pose.theta)
        cos_heading = math.cos(heading)
        sin_heading = math.sin(heading)

        return [
            vx * cos_heading - vy * sin_heading,
            vx * sin_heading + vy * cos_heading
        ]

    def body_to_wheels(self, vx, vy, omega):
        wheel_speeds = []

        for angle in self.wheel_angles:
            phi = math.radians(angle)
            wheel_speeds.append(
                -math.sin(phi) * vx
                + math.cos(phi) * vy
                + self.base_radius * omega
            )

        return self.limit_wheel_speeds(wheel_speeds)

    def wheels_to_body(self, wheel_speeds):
        w0, w1, w2 = wheel_speeds
        vx = (w2 - w1) / math.sqrt(3)
        vy = (2 * w0 - w1 - w2) / 3
        omega = (w0 + w1 + w2) / (3 * self.base_radius)

        return [vx, vy, omega]

    def limit_wheel_speeds(self, wheel_speeds):
        largest = max(abs(speed) for speed in wheel_speeds)
        if largest <= self.max_wheel_speed:
            return wheel_speeds

        scale = self.max_wheel_speed / largest
        return [speed * scale for speed in wheel_speeds]

    def set_desired_world_velocity(self, vx, vy, omega):
        vx_body, vy_body = self.world_to_body(vx, vy)
        self.target_wheel_speeds = self.body_to_wheels(vx_body, vy_body, omega)

    def set_desired_body_velocity(self, vx, vy, omega):
        self.target_wheel_speeds = self.body_to_wheels(vx, vy, omega)

    def update_wheel_speeds(self, delta):
        max_change = self.max_wheel_acceleration * delta

        for i, target_speed in enumerate(self.target_wheel_speeds):
            current_speed = self.wheel_speeds[i]
            change = self.clamp(
                target_speed - current_speed,
                -max_change,
                max_change
            )
            self.wheel_speeds[i] = current_speed + change

    def get_effective_wheel_speeds(self):
        inaccuracy = self.settings.wheel_inaccuracy
        return [
            speed * (1 + error * inaccuracy)
            for speed, error in zip(self.wheel_speeds, self.wheel_error_profile)
        ]

    def tick(self, delta):
        self.update_wheel_speeds(delta)
        vx_body, vy_body, omega = self.wheels_to_body(self.get_effective_wheel_speeds())
        vx_world, vy_world = self.body_to_world(vx_body, vy_body)
        self.velocity = [vx_world, vy_world, omega]

        return self.velocity

    def get_wheel_global_pose(self, angle):
        heading = math.radians(self.agent.pose.theta)
        local_angle = math.radians(angle)
        local_x = self.base_radius * math.cos(local_angle)
        local_y = self.base_radius * math.sin(local_angle)

        x = self.agent.pose.x + local_x * math.cos(heading) - local_y * math.sin(heading)
        y = self.agent.pose.y + local_x * math.sin(heading) + local_y * math.cos(heading)
        theta = self.agent.pose.theta + angle + 90

        return Pose(x, y, theta)

    def get_rotated_rect_points(self, center_x, center_y, width, height, theta):
        half_width = width / 2
        half_height = height / 2
        angle = math.radians(theta)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        points = []
        for x, y in [
            (-half_width, -half_height),
            (half_width, -half_height),
            (half_width, half_height),
            (-half_width, half_height)
        ]:
            points.append((
                center_x + x * cos_angle - y * sin_angle,
                center_y + x * sin_angle + y * cos_angle
            ))

        return points

    def draw(self, screen, show_wheel_speeds=True):
        for angle, speed in zip(self.wheel_angles, self.get_effective_wheel_speeds()):
            wheel_pose = self.get_wheel_global_pose(angle)
            wheel_points = self.get_rotated_rect_points(
                wheel_pose.x,
                wheel_pose.y,
                self.wheel_diameter,
                self.wheel_width,
                wheel_pose.theta
            )

            pygame.draw.polygon(screen, "#000000", wheel_points)
            # pygame.draw.polygon(screen, "#111111", wheel_points, 2)

            if show_wheel_speeds:
                drive_angle = math.radians(wheel_pose.theta)
                speed_scale = 0 if self.max_wheel_speed == 0 else abs(speed**1.2) / self.max_wheel_speed
                direction = 1 if speed >= 0 else -1
                start = (wheel_pose.x, wheel_pose.y)
                end = (
                    wheel_pose.x + math.cos(drive_angle) * (speed_scale*direction) * 12,
                    wheel_pose.y + math.sin(drive_angle) * (speed_scale*direction) * 12
                )
                if direction > 0:
                    pygame.draw.line(screen, "#ff0000", start, end, 3)
                else:
                    pygame.draw.line(screen, "#00ffff", start, end, 3)
