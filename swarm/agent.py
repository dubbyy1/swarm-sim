import pygame
import math
import time
import networkx as nx

from .utils import Pose
from .types import Formation, State, Intent
from .components import IREmitter, IRReceiver, UWBAntenna, Radio

class Agent:
    def __init__(self, id, network, screen):
        self.id = id
        self.network = network
        self.screen = screen

        self.pose = Pose(0, 0, 0)
        self.radius = 20
        self.speed = 50
        self.emitter_radius = 2
        self.emitters = self.spawn_emitters(3)
        self.receiver_radius = 21
        self.receivers = self.spawn_receivers(16)
        self.antenna = UWBAntenna(self, self.network)
        self.radio = Radio(self, self.network)

        self.map: dict[int, dict] = {}
        self.local_network = nx.Graph()
        self.local_network.add_node(self.id)

        self.recency_window = 0.5
        self.network_edge_window = 0.5
        self.ir_top_k = 3
        self.bearing_smoothing = 0.35
        self.distance_smoothing = 0.35
        self.pose_smoothing = 0.25
        self.pending_ir = {}
        self.pending_radio = []
        self.message_id = 0

        self.initialized = False
        self.leader = False
        self.formation_controller = FormationController(self, screen)
        self.formation = Formation.LINE
        self.state = State.IDLE

    def start(self):
        if self.get_live_neighbours():
            self.update_own_network_connections()
            self.leader = True
            self.transmit_radio(self.form_radio(
                intent=Intent.JOIN_NETWORK
            ))
            self.initialized = True

    ### COMPONENTS

    def get_ring_pose(self, radius, index, length):
        theta = index * 360 / length
        x = radius * math.cos(math.radians(theta))
        y = radius * math.sin(math.radians(theta))

        return Pose(x, y, theta)

    def spawn_emitters(self, count):
        res = []
        for i in range(count):
            e = IREmitter(self, self.network, i)
            e.set_pose(self.get_ring_pose(
                self.emitter_radius,
                i,
                count
            ))
            res.append(e)
        return res

    def spawn_receivers(self, count):
        res = []
        for i in range(count):
            r = IRReceiver(self, self.network, i)
            r.set_pose(self.get_ring_pose(
                self.receiver_radius,
                i,
                count
            ))
            res.append(r)
        return res

    ### FLOW

    def tick(self, delta):
        self.read_ir(delta)
        self.read_radio(delta)

        if self.state in (State.IN_FORMATION, State.EXCLUDED):
            velocity = self.formation_controller.get_formation_velocity()
            self.pose.x += velocity[0] * delta
            self.pose.y += velocity[1] * delta

    def communicate(self):
        self.ping()
        if not self.initialized:
            self.start()

    def ping(self):
        ir_packet = self.form_ir()
        for emitter in self.emitters:
            emitter.emit(ir_packet.copy())

        self.antenna.transmit(self.form_uwb())

    ### RADIO

    def form_radio(self, intent, payload=None):
        self.message_id += 1
        self.message_id %= 256

        packet = {
            "sender_id": self.id,
            "message_id": self.message_id
        }
        match intent:
            case Intent.JOIN_NETWORK:
                self.initialized = True
                packet["intent"] = Intent.JOIN_NETWORK

                neighbours = self.get_live_neighbours()
                live = list(payload.get("live", [])) if payload else []

                if self.id not in live:
                    live.append(self.id)

                next_agent = -1
                for neighbour_id in neighbours:
                    if neighbour_id not in live:
                        next_agent = neighbour_id
                        break

                packet["neighbours"] = neighbours
                packet["distances"] = [self.get_agent_distance(neighbour_id) for neighbour_id in neighbours]
                packet["live"] = live
                packet["next"] = next_agent

            case Intent.SET_FORMATION_ORDER:
                packet["intent"] = Intent.SET_FORMATION_ORDER
                order = self.formation_controller.get_formation_order(
                    self.local_network, self.formation
                )
                self.set_formation_order(order)
                packet["state"] = self.state
                packet["order"] = order
                print(packet)

            case _:
                pass
        return packet

    def transmit_radio(self, packet):
        self.radio.broadcast(packet)

    def receive_radio(self, packet):
        self.pending_radio.append(dict(packet))

    def read_radio(self, delta):
        messages = self.pending_radio
        self.pending_radio = []

        for packet in messages:
            self.process_radio(packet)

    def update_network_edge(self, a, b, distance):
        current_time = time.time()

        self.local_network.add_node(a)
        self.local_network.add_node(b)

        if self.local_network.has_edge(a, b):
            edge = self.local_network.get_edge_data(a, b)
            edge_age = current_time - edge["timestamp"]

            if edge_age <= self.network_edge_window:
                existing_distance = edge["distance"]
                distance = (existing_distance + distance) / 2

        self.local_network.add_edge(a, b, distance=distance, timestamp=current_time)

    def update_own_network_connections(self):
        for neighbour_id in self.get_live_neighbours():
            self.update_network_edge(
                self.id,
                neighbour_id,
                self.get_agent_distance(neighbour_id)
            )

    def process_radio(self, packet):
        sender_id = packet.get("sender_id")
        if sender_id == self.id:
            return

        if packet.get("intent") == Intent.JOIN_NETWORK:
            self.leader = False

        match packet.get("intent"):
            case Intent.JOIN_NETWORK:
                neighbours = packet.get("neighbours", [])
                distances = packet.get("distances", [])

                for neighbour_id, distance in zip(neighbours, distances):
                    self.update_network_edge(sender_id, neighbour_id, distance)

                live = packet.get("live", [])
                next_agent = packet.get("next", -1)

                if self.id == next_agent or (next_agent == -1 and self.id not in live):
                    self.update_own_network_connections()
                    self.leader = True
                    self.transmit_radio(self.form_radio(
                        intent=Intent.JOIN_NETWORK,
                        payload={"live": live}
                    ))
            case Intent.SET_FORMATION:
                self.set_formation(packet["formation"])
                if self.leader:
                    print(self.id, "LEADER")
                    self.transmit_radio(self.form_radio(
                        intent=Intent.SET_FORMATION_ORDER
                    ))
            case Intent.SET_FORMATION_ORDER:
                self.set_formation_order(packet.get("order", []))
            case _:
                pass

    ### INFRARED

    def form_ir(self):
        self.message_id += 1
        self.message_id %= 256

        return [
            0xF8,
            self.id,
            self.message_id
        ]

    def receive_ir(self, receiver_id, packet, signal_strength):
        _, sender_id, message_id, emitter_id, _ = packet
        message_key = (sender_id, message_id)

        if message_key not in self.pending_ir:
            self.pending_ir[message_key] = {
                "packet": packet,
                "detections": [],
                "age": 0
            }

        self.pending_ir[message_key]["detections"].append({
            "emitter_id": emitter_id,
            "receiver_id": receiver_id,
            "signal_strength": signal_strength
        })

    def clean_ir(self, message):
        emitters:dict[int,int] = {}
        for detection in message["detections"]:
            emitter_id = detection["emitter_id"]
            emitters.setdefault(emitter_id, 0)
            emitters[emitter_id] += 1

        dominant_emitter = max(emitters, key=lambda emitter_id: emitters[emitter_id])

        strengths = {i: 0 for i in range(len(self.receivers))}

        for detection in message["detections"]:
            if detection["emitter_id"] != dominant_emitter:
                continue

            receiver_id = detection["receiver_id"]
            strengths[receiver_id] = detection["signal_strength"]

        return {
            "packet": message["packet"],
            "strengths": strengths
        }

    def read_ir(self, delta):
        completed_messages = []

        for message_key, message in self.pending_ir.items():
            message["age"] += delta
            if message["age"] >= self.recency_window:
                completed_messages.append(message_key)

        for message_key in completed_messages:
            message = self.clean_ir(self.pending_ir.pop(message_key))

            self.process_ir(message)

    def process_ir(self, message):
        sender_id = message["packet"][1]

        bearing = self.estimate_ir_bearing(message["strengths"])

        if bearing is None:
            return

        entry = self.get_map_entry(sender_id)

        if entry["ir_timestamp"] == 0:
            entry["bearing"] = bearing
        else:
            entry["bearing"] = self.smooth_bearing(
                entry["bearing"],
                bearing,
                self.bearing_smoothing
            )

        entry["ir_timestamp"] = time.time()
        self.update_map_pose(entry)

    ### UWB

    def form_uwb(self):
        return [self.id]

    def receive_uwb(self, packet, distance):
        sender_id = packet[0]
        self.process_uwb(sender_id, distance)

    def process_uwb(self, sender_id, distance):
        entry = self.get_map_entry(sender_id)

        if entry["uwb_timestamp"] == 0:
            entry["distance"] = distance
        else:
            entry["distance"] = self.smooth_value(
                entry["distance"],
                distance,
                self.distance_smoothing
            )

        entry["uwb_timestamp"] = time.time()
        self.update_map_pose(entry)

    def get_live_neighbours(self, max_age=0.5):
        now = time.time()
        neighbours = []

        for agent_id, entry in self.map.items():
            if agent_id == self.id:
                continue

            last_seen = max(entry["ir_timestamp"], entry["uwb_timestamp"])
            if now - last_seen < max_age:
                neighbours.append(agent_id)

        return neighbours

    ### LOCATION PROCESSING
    def estimate_ir_bearing(self, strengths):
        readings = [
            (receiver_id, strength)
            for receiver_id, strength in strengths.items()
            if strength > 0
        ]
        readings.sort(key=lambda reading: reading[1], reverse=True)
        readings = readings[:self.ir_top_k]

        total_strength = sum(strength for _, strength in readings)
        if total_strength == 0:
            return None

        total_x = 0
        total_y = 0

        for receiver_id, strength in readings:
            normalized_strength = strength / total_strength
            receiver_pose = self.receivers[receiver_id].get_pose()
            total_x += receiver_pose.x * normalized_strength
            total_y += receiver_pose.y * normalized_strength

        if total_x == 0 and total_y == 0:
            return None

        return math.degrees(math.atan2(total_y, total_x)) % 360

    def get_relative_pose(self, distance, bearing):
        x = distance * math.cos(math.radians(bearing))
        y = distance * math.sin(math.radians(bearing))
        return Pose(x, y, bearing)

    def smooth_value(self, current, target, alpha):
        return current + (target - current) * alpha

    def smooth_bearing(self, current, target, alpha):
        difference = (target - current + 180) % 360 - 180
        return (current + difference * alpha) % 360

    def update_map_pose(self, entry):
        if entry["ir_timestamp"] == 0 or entry["uwb_timestamp"] == 0:
            return

        target_pose = self.get_relative_pose(entry["distance"], entry["bearing"])
        current_pose = entry["pose"]

        if current_pose.x == 0 and current_pose.y == 0:
            entry["pose"] = target_pose
            return

        alpha = self.pose_smoothing
        x = current_pose.x + (target_pose.x - current_pose.x) * alpha
        y = current_pose.y + (target_pose.y - current_pose.y) * alpha

        if x == 0 and y == 0:
            theta = target_pose.theta
        else:
            theta = math.degrees(math.atan2(y, x)) % 360

        entry["pose"] = Pose(x, y, theta)

    ### UTILS

    def get_map_entry(self, agent_id):
        if agent_id not in self.map:
            self.map[agent_id] = {
                "ir_timestamp": 0.0,
                "uwb_timestamp": 0.0,
                "bearing": 0.0,
                "distance": 0.0,
                "pose": Pose(0, 0, 0)
            }
        return self.map[agent_id]

    def get_agent_distance(self, agent_id):
        return self.map[agent_id]["distance"]

    def set_pose(self, pose):
        self.pose = pose
    def get_pose(self):
        return self.pose
    def set_formation(self, formation):
        self.formation = formation

    def set_formation_order(self, order):
        if self.id not in order:
            self.state = State.EXCLUDED
            self.formation_controller.neighbours = tuple()
            return

        self.state = State.IN_FORMATION
        index = order.index(self.id)
        neighbours = []

        match self.formation:
            case Formation.CIRCLE:
                if len(order) == 2:
                    neighbours.append(order[1 - index])
                elif len(order) > 2:
                    neighbours.append(order[index - 1])
                    neighbours.append(order[(index + 1) % len(order)])
            case _:
                if index > 0:
                    neighbours.append(order[index - 1])
                if index < len(order) - 1:
                    neighbours.append(order[index + 1])

        self.formation_controller.order = tuple(order)
        self.formation_controller.neighbours = tuple(neighbours)

    def draw(self, screen):
        pygame.draw.circle(screen, "#000000", (int(self.pose.x), int(self.pose.y)), self.radius, 2)

        if self.id == -1:
            pygame.draw.circle(screen, "#ff00ff", (int(self.pose.x), int(self.pose.y)), self.radius, 2)
            ln = self.get_live_neighbours()
            for agent_id, entry in self.map.items():
                if agent_id == self.id:
                    continue
                if agent_id not in ln:
                    continue

                relative_pose = entry["pose"]
                debug_x = self.pose.x + relative_pose.x
                debug_y = self.pose.y + relative_pose.y
                pygame.draw.circle(screen, "#ff00ff", (debug_x, debug_y), 4)

        for emitter in self.emitters:
            emitter.draw(screen)
        for receiver in self.receivers:
            receiver.draw(screen)
        # self.antenna.draw(screen)
        # self.radio.draw(screen)

class FormationController:
    def __init__(self, agent, screen):
        self.agent = agent
        self.screen = screen
        self.neighbours = tuple()
        self.order = tuple()
        self.min_neighbour_distance = self.agent.radius * 5
        self.collision_avoidance_strength = 1.0

    def get_formation_velocity(self):
        movement_neighbours = self.neighbours

        def get_formation_neighbour_positions():
            neighbour_positions = []

            for neighbour_id in self.neighbours:
                if neighbour_id not in self.agent.map:
                    continue

                neighbour_positions.append(self.agent.map[neighbour_id]["pose"])

            return neighbour_positions

        def get_line_position():
            neighbour_positions = get_formation_neighbour_positions()

            if len(neighbour_positions) == 0:
                return None
            if len(neighbour_positions) == 1:
                return neighbour_positions[0]

            x = sum(position.x for position in neighbour_positions) / len(neighbour_positions)
            y = sum(position.y for position in neighbour_positions) / len(neighbour_positions)
            return Pose(x, y, 0)

        def get_circle_position():
            neighbour_positions = get_formation_neighbour_positions()

            if len(neighbour_positions) == 0:
                return None
            if len(neighbour_positions) == 1:
                return neighbour_positions[0]

            circle_size = len(self.order)
            if circle_size < 3:
                return get_line_position()

            a = neighbour_positions[0]
            b = neighbour_positions[1]
            dx = b.x - a.x
            dy = b.y - a.y
            chord = math.hypot(dx, dy)

            if chord == 0:
                return None

            midpoint_x = (a.x + b.x) / 2
            midpoint_y = (a.y + b.y) / 2
            spacing = self.min_neighbour_distance
            radius = spacing / (2 * math.sin(math.pi / circle_size))
            expected_chord = 2 * radius * math.sin(2 * math.pi / circle_size)
            expected_half_chord = expected_chord / 2
            height = math.sqrt(max(0, spacing * spacing - expected_half_chord * expected_half_chord))
            perpendicular_x = -dy / chord
            perpendicular_y = dx / chord
            candidates = [
                Pose(
                    midpoint_x + perpendicular_x * height,
                    midpoint_y + perpendicular_y * height,
                    0
                ),
                Pose(
                    midpoint_x - perpendicular_x * height,
                    midpoint_y - perpendicular_y * height,
                    0
                )
            ]

            sum_x = 0
            sum_y = 0

            for neighbour_id in self.agent.get_live_neighbours():
                if neighbour_id not in self.agent.map:
                    continue

                neighbour_pose = self.agent.map[neighbour_id]["pose"]
                sum_x += neighbour_pose.x
                sum_y += neighbour_pose.y

            return max(
                candidates,
                key=lambda pose: math.hypot(pose.x - sum_x, pose.y - sum_y)
            )

        def get_excluded_position():
            nonlocal movement_neighbours

            neighbours = self.agent.get_live_neighbours()
            if not neighbours:
                return None

            neighbour_id = neighbours[0]
            if neighbour_id not in self.agent.map:
                return None

            movement_neighbours = (neighbour_id,)
            return self.agent.map[neighbour_id]["pose"]

        if self.agent.state == State.EXCLUDED:
            target = get_excluded_position()
        else:
            match self.agent.formation:
                case Formation.LINE:
                    target = get_line_position()
                case Formation.CIRCLE:
                    target = get_circle_position()
                case _:
                    return [0, 0]

        if target is None:
            return [0, 0]

        global_target = Pose(target.x, target.y, target.theta) + self.agent.pose
        pygame.draw.circle(self.screen, "#ff00ff", (int(global_target.x), int(global_target.y)), 3)
        target_distance = math.hypot(target.x, target.y)
        if target_distance == 0:
            velocity = [0, 0]
        else:
            desired_gap = self.min_neighbour_distance if len(movement_neighbours) == 1 else 0
            move_distance = max(target_distance - desired_gap, 0)
            speed = min(self.agent.speed, move_distance)
            velocity = [
                target.x / target_distance * speed,
                target.y / target_distance * speed
            ]

        for neighbour_id in self.agent.get_live_neighbours():
            if neighbour_id not in self.agent.map:
                continue

            neighbour_pose = self.agent.map[neighbour_id]["pose"]
            distance = math.hypot(neighbour_pose.x, neighbour_pose.y)

            if distance == 0 or distance >= self.min_neighbour_distance:
                continue

            push = min(
                self.agent.speed,
                (self.min_neighbour_distance - distance) * self.collision_avoidance_strength
            )
            velocity[0] -= neighbour_pose.x / distance * push
            velocity[1] -= neighbour_pose.y / distance * push

        return velocity

    def get_cycle_distance(self, network: nx.Graph, cycle):
        if len(cycle) < 2:
            return 0

        return self.get_path_distance(network, cycle) + network[cycle[-1]][cycle[0]].get("distance", 1)
    def normalize_cycle_direction(self, cycle):
        if not cycle:
            return []

        rotations = []
        directions = [list(cycle), list(reversed(cycle))]

        for direction in directions:
            for index in range(len(direction)):
                rotations.append(direction[index:] + direction[:index])

        return min(rotations)
    def get_best_cycle(self, network: nx.Graph):
        best_cycle = []
        best_distance = 0
        seen_cycles = set()
        components = sorted(nx.connected_components(network), key=len, reverse=True)

        for component_nodes in components:
            component = network.subgraph(component_nodes)
            if component.number_of_nodes() < 3:
                continue

            for start in sorted(component.nodes):
                stack = [(start, [start])]

                while stack:
                    node, path = stack.pop()

                    for neighbour in sorted(component.neighbors(node), reverse=True):
                        if neighbour == start and len(path) >= 3:
                            normalized_cycle = self.normalize_cycle_direction(path)
                            cycle_key = tuple(normalized_cycle)

                            if cycle_key in seen_cycles:
                                continue

                            seen_cycles.add(cycle_key)
                            cycle_distance = self.get_cycle_distance(component, normalized_cycle)

                            if (
                                len(normalized_cycle) > len(best_cycle)
                                or (
                                    len(normalized_cycle) == len(best_cycle)
                                    and (
                                        cycle_distance < best_distance
                                        or (
                                            cycle_distance == best_distance
                                            and normalized_cycle < self.normalize_cycle_direction(best_cycle)
                                        )
                                    )
                                )
                            ):
                                best_cycle = normalized_cycle
                                best_distance = cycle_distance

                            continue

                        if neighbour in path:
                            continue

                        stack.append((neighbour, path + [neighbour]))

        return best_cycle

    def get_path_distance(self, network: nx.Graph, path):
        distance = 0

        for a, b in zip(path, path[1:]):
            distance += network[a][b].get("distance", 1)

        return distance
    def normalize_path_direction(self, path):
        reversed_path = list(reversed(path))
        return min(path, reversed_path)
    def get_best_path(self, network: nx.Graph):
        best_path = []
        best_distance = 0

        components = sorted(nx.connected_components(network), key=len, reverse=True)

        for component_nodes in components:
            component = network.subgraph(component_nodes)

            for start in sorted(component.nodes):
                stack = [(start, [start])]

                while stack:
                    node, path = stack.pop()
                    normalized_path = self.normalize_path_direction(path)
                    path_distance = self.get_path_distance(component, path)

                    if (
                        len(path) > len(best_path)
                        or (
                            len(path) == len(best_path)
                            and (
                                path_distance < best_distance
                                or (
                                    path_distance == best_distance
                                    and normalized_path < self.normalize_path_direction(best_path)
                                )
                            )
                        )
                    ):
                        best_path = normalized_path
                        best_distance = path_distance

                    for neighbour in sorted(component.neighbors(node), reverse=True):
                        if neighbour in path:
                            continue

                        stack.append((neighbour, path + [neighbour]))

        return best_path

    def get_formation_order(self, network:nx.Graph, formation:Formation):
        match formation:
            case Formation.LINE:
                return self.get_best_path(network)
            case Formation.CIRCLE:
                return self.get_best_cycle(network)
            case _:
                pass
        return []
