import math
import random

class Network:
    def __init__(self, world, screen, settings):
        self.world = world
        self.screen = screen
        self.settings = settings
        self.ir_intensity_dropoff = 100.0

    def broadcast_radio(self, packet):
        sender_id = packet.get("sender_id")

        for agent in self.world.agents:
            if agent.id == sender_id:
                continue

            agent.radio.receive(packet)

    def broadcast_uwb(self, sender_pose, packet):
        sender_id = packet[0]

        for agent in self.world.agents:
            if agent.id == sender_id:
                continue

            receiver_pose = agent.antenna.get_global_pose()
            distance = sender_pose.distance_to(receiver_pose)
            noisy_distance = max(0, distance + random.gauss(0, self.settings.uwb_distance_noise))
            agent.antenna.receive(packet, noisy_distance)

    def broadcast_ir(self, sender_pose, packet, cone_width, sglobal):
        _, sender_id, message_id, emitter_id, _ = packet
        for agent in self.world.agents:
            if agent.id == sender_id:
                continue
            for receiver in agent.receivers:
                receiver_pose = receiver.get_global_pose()

                distance = sender_pose.distance_to(receiver_pose)
                if distance > self.settings.ir_max_range:
                    continue

                if not self.receiver_is_in_cone(sender_pose, receiver_pose, cone_width):
                    continue
                if self.signal_is_blocked(sender_pose, receiver_pose, sender_id, agent.id):
                    continue

                strength = self.get_signal_strength(distance)
                noisy_strength = max(0, min(1, strength + random.gauss(0, self.settings.ir_noise)))
                receiver.receive(packet, noisy_strength)


    def receiver_is_in_cone(self, sender_pose, receiver_pose, cone_width):
        direction_to_receiver = sender_pose.direction_to(receiver_pose, deg=True)
        angle_offset = abs(self.get_angle_difference(direction_to_receiver, sender_pose.theta))

        return angle_offset <= cone_width / 2

    def get_signal_strength(self, distance):
        return 1 / (1 + distance / self.ir_intensity_dropoff)

    def signal_is_blocked(self, sender_pose, receiver_pose, sender_id, receiver_agent_id):
        for agent in self.world.agents:
            if agent.id == sender_id:
                continue

            if not self.segment_intersects_agent(
                sender_pose.x,
                sender_pose.y,
                receiver_pose.x,
                receiver_pose.y,
                agent,
                allow_endpoint=agent.id == receiver_agent_id
            ):
                continue

            return True

        return False

    def segment_intersects_agent(self, x1, y1, x2, y2, agent, allow_endpoint=False):
        cx, cy, ct = agent.get_pose().unwrap()
        radius = agent.radius
        dx = x2 - x1
        dy = y2 - y1
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return math.hypot(cx - x1, cy - y1) < radius

        t = ((cx - x1) * dx + (cy - y1) * dy) / length_squared
        t = max(0, min(1, t))

        if allow_endpoint and t > 0.98:
            return False

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return math.hypot(cx - closest_x, cy - closest_y) < radius

    def get_angle_difference(self, a, b):
        return (a - b + 180) % 360 - 180
