from .network import Network
from .controller import Controller
from .agent import Agent

from .types import Formation
from .utils import Pose

import random
import pygame

class World:
    def __init__(self, size:int, screen):
        self.screen = screen
        self.network = Network(self, screen)
        self.controller = Controller(self, self.network)
        self.default_size = size
        self.agents:list[Agent] = []

        self.spawn(size)

    def spawn(self, size, x=None, y=None):
        for i in range(size):
            agent = Agent(
                id=len(self.agents),
                network=self.network,
                screen=self.screen,
            )
            if x is not None and y is not None:
                agent.set_pose(Pose(x, y, 0))
            else:
                width, height = self.screen.get_size()
                spawn_x = random.uniform(agent.radius, width - agent.radius)
                spawn_y = random.uniform(agent.radius, height - agent.radius)
                agent.set_pose(Pose(spawn_x, spawn_y, 0))
            self.agents.append(agent)

    def purge(self):
        self.agents = []

    def refresh(self):
        self.purge()
        self.spawn(self.default_size)

    def set_formation(self, formation:Formation):
        self.controller.set_formation(formation)

    def tick(self, delta):
        for agent in self.agents:
            agent.communicate()
        # print("Comms over")
        for agent in self.agents:
            agent.tick(delta)
        # print("Action over")

    def draw(self, screen):
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

        for a, b in graph_edges:
            agent_a = agents_by_id[a]
            agent_b = agents_by_id[b]
            pygame.draw.line(
                screen,
                "#00aa00",
                (agent_a.pose.x, agent_a.pose.y),
                (agent_b.pose.x, agent_b.pose.y),
                1
            )

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
