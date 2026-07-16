from .network import Network
from .controller import Controller
from .agent import Agent

from .types import Formation
from .utils import Pose
from .settings import Settings

import math
import random
import pygame

class World:
    def __init__(self, size:int, screen, settings: Settings | None = None):
        self.screen = screen
        self.settings = settings if settings is not None else Settings(reset_swarm_size=size)
        self.network = Network(self, screen, self.settings)
        self.controller = Controller(self, self.network)
        self.default_size = size
        self.settings.reset_swarm_size = size
        self.selected_agent: Agent | None = None
        self.walls: list[tuple[float, float, float, float]] = []
        self.wall_mode_enabled = False
        self.pending_wall_start: tuple[float, float] | None = None
        self.agents:list[Agent] = []

        self.spawn(size)

    def spawn(self, size, x=None, y=None):
        for i in range(size):
            agent = Agent(
                id=len(self.agents),
                network=self.network,
                screen=self.screen,
                settings=self.settings,
                emitter_count=self.settings.reset_emitter_count,
                receiver_count=self.settings.reset_receiver_count,
            )
            if x is not None and y is not None:
                agent.set_pose(Pose(x, y, 0))
            else:
                width, height = self.screen.get_size()
                spawn_x = random.uniform(agent.radius, width - agent.radius)
                spawn_y = random.uniform(agent.radius, height - agent.radius)
                agent.set_pose(Pose(spawn_x, spawn_y, 0))
            self.agents.append(agent)

        self.elect_global_leader()

    def purge(self):
        self.deselect_agent()
        self.agents = []

    def refresh(self):
        self.default_size = self.settings.reset_swarm_size
        self.settings.remote_control_enabled = False
        self.purge()
        self.spawn(self.default_size)

    def set_reset_swarm_size(self, size):
        self.settings.reset_swarm_size = max(1, int(size))

    def set_reset_emitter_count(self, count):
        self.settings.reset_emitter_count = max(1, int(count))

    def set_reset_receiver_count(self, count):
        self.settings.reset_receiver_count = max(1, int(count))

    def set_formation(self, formation:Formation):
        self.elect_global_leader()
        self.controller.set_formation(formation)

    def toggle_wall_mode(self):
        self.wall_mode_enabled = not self.wall_mode_enabled
        self.pending_wall_start = None

    def clear_walls(self):
        self.walls = []
        self.pending_wall_start = None

    def handle_wall_click(self, position):
        x, y = position

        if self.pending_wall_start is None:
            self.pending_wall_start = (float(x), float(y))
            return

        start_x, start_y = self.pending_wall_start
        end_x = float(x)
        end_y = float(y)

        if start_x != end_x or start_y != end_y:
            self.walls.append((start_x, start_y, end_x, end_y))

        self.pending_wall_start = None

    def elect_global_leader(self):
        if not self.agents:
            return

        leader = min(self.agents, key=lambda agent: agent.id)
        for agent in self.agents:
            agent.leader = agent == leader

    def get_agent_at(self, position):
        x, y = position

        for agent in reversed(self.agents):
            dx = agent.pose.x - x
            dy = agent.pose.y - y

            if dx * dx + dy * dy <= agent.radius * agent.radius:
                return agent

        return None

    def select_agent(self, agent):
        if self.selected_agent is not None and self.selected_agent != agent:
            self.selected_agent.exit_remote()

        self.selected_agent = agent

        if self.settings.remote_control_enabled:
            agent.enter_remote()
        else:
            agent.exit_remote()

    def deselect_agent(self):
        if self.selected_agent is not None:
            self.selected_agent.exit_remote()
        self.selected_agent = None

    def select_agent_at(self, position):
        agent = self.get_agent_at(position)

        if agent is None:
            self.deselect_agent()
            return False

        self.select_agent(agent)
        return True

    def toggle_remote_control(self):
        self.set_remote_control_enabled(not self.settings.remote_control_enabled)

    def set_remote_control_enabled(self, enabled):
        if self.selected_agent is None:
            return

        self.settings.remote_control_enabled = enabled

        if enabled:
            self.selected_agent.enter_remote()
        else:
            self.selected_agent.exit_remote()

    def tick(self, delta):
        self.elect_global_leader()
        for agent in self.agents:
            agent.communicate()
        for agent in self.agents:
            agent.tick(delta)
        self.elect_global_leader()
        self.resolve_collisions()

    def resolve_collisions(self):
        for _ in range(self.settings.collision_iterations):
            for i, agent_a in enumerate(self.agents):
                for agent_b in self.agents[i + 1:]:
                    dx = agent_b.pose.x - agent_a.pose.x
                    dy = agent_b.pose.y - agent_a.pose.y
                    distance = math.hypot(dx, dy)
                    min_distance = agent_a.radius + agent_b.radius

                    if distance >= min_distance:
                        continue

                    if distance == 0:
                        dx = 1
                        dy = 0
                        distance = 1

                    overlap = min_distance - distance
                    push_x = dx / distance * overlap / 2
                    push_y = dy / distance * overlap / 2

                    agent_a.pose.x -= push_x
                    agent_a.pose.y -= push_y
                    agent_b.pose.x += push_x
                    agent_b.pose.y += push_y

            for agent in self.agents:
                self.resolve_wall_collision(agent)

    def resolve_wall_collision(self, agent):
        for x1, y1, x2, y2 in self.walls:
            closest_x, closest_y = self.get_closest_point_on_segment(
                agent.pose.x,
                agent.pose.y,
                x1,
                y1,
                x2,
                y2
            )
            dx = agent.pose.x - closest_x
            dy = agent.pose.y - closest_y
            distance = math.hypot(dx, dy)

            if distance >= agent.radius:
                continue

            if distance == 0:
                wall_dx = x2 - x1
                wall_dy = y2 - y1
                wall_length = math.hypot(wall_dx, wall_dy)
                if wall_length == 0:
                    dx = 1
                    dy = 0
                else:
                    dx = -wall_dy / wall_length
                    dy = wall_dx / wall_length
                distance = 1

            overlap = agent.radius - distance
            agent.pose.x += dx / distance * overlap
            agent.pose.y += dy / distance * overlap

    def get_closest_point_on_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return x1, y1

        t = ((px - x1) * dx + (py - y1) * dy) / length_squared
        t = max(0, min(1, t))
        return x1 + t * dx, y1 + t * dy

    def draw(self, screen):
        if self.settings.show_ir_range_circle and self.selected_agent is not None:
            pygame.draw.circle(
                screen,
                "#ff8800",
                (int(self.selected_agent.pose.x), int(self.selected_agent.pose.y)),
                int(self.settings.ir_max_range),
                1
            )

        for wall in self.walls:
            pygame.draw.line(
                screen,
                "#000000",
                (wall[0], wall[1]),
                (wall[2], wall[3]),
                4
            )

        if self.pending_wall_start is not None:
            pygame.draw.circle(
                screen,
                "#000000",
                (int(self.pending_wall_start[0]), int(self.pending_wall_start[1])),
                5,
                1
            )

        agents_by_id = {agent.id: agent for agent in self.agents}
        graph_edges = set()
        formation_edges = set()

        for agent in self.agents:
            for a, b in agent.local_network.edges:
                if a in agents_by_id and b in agents_by_id:
                    graph_edges.add(tuple(sorted((a, b))))

            for neighbour_id in agent.formation_controller.neighbours:
                if neighbour_id in agents_by_id:
                    formation_edges.add(tuple(sorted((agent.id, neighbour_id))))

        if self.settings.show_network_lines:
            for a, b in graph_edges:
                agent_a = agents_by_id[a]
                agent_b = agents_by_id[b]
                pygame.draw.line(
                    screen,
                    "#00ff00",
                    (agent_a.pose.x, agent_a.pose.y),
                    (agent_b.pose.x, agent_b.pose.y),
                    1
                )

        if self.settings.show_formation_lines:
            for a, b in formation_edges:
                agent_a = agents_by_id[a]
                agent_b = agents_by_id[b]
                pygame.draw.line(
                    screen,
                    "#00ff00",
                    (agent_a.pose.x, agent_a.pose.y),
                    (agent_b.pose.x, agent_b.pose.y),
                    3
                )
