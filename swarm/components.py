import math
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

    def draw(self, screen):
        global_pose = self.get_global_pose()
        pygame.draw.circle(screen, (255, 0, 0), (global_pose.x, global_pose.y), 2.5)

        # theta = math.radians(global_pose.theta)
        # half_cone = math.radians(self.cone_width / 2)
        # cone_length = 500
        # cone_points = [
        #     (global_pose.x, global_pose.y),
        #     (
        #         global_pose.x + cone_length * math.cos(theta + half_cone),
        #         global_pose.y + cone_length * math.sin(theta + half_cone),
        #     ),
        #     (
        #         global_pose.x + cone_length * math.cos(theta - half_cone),
        #         global_pose.y + cone_length * math.sin(theta - half_cone),
        #     ),
        # ]

        # cone_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        # pygame.draw.polygon(cone_surface, (255, 0, 0, 10), cone_points)
        # screen.blit(cone_surface, (0, 0))


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
