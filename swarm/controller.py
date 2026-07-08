from .types import Intent
from .components import IREmitter

class Controller:
    def __init__(self, world, network):
        self.world = world
        self.network = network

        self.message_id = 0
        self.emitter = IREmitter(self, self.network, 0)

    def form_packet(self):
        return {
            "sender_id": -1,
            "message_id": self.message_id,
            "intent": Intent.SET_FORMATION,
            "formation": self.formation
        }

    def form_ir(self):
        self.message_id += 1
        return [
            0xF8,
            0xFF,
            self.message_id
        ]

    def broadcast(self, packet):
        self.network.broadcast_radio(packet)

    def ping(self):
        self.emitter.emit(self.form_ir())

    def set_formation(self, formation):
        self.formation = formation
        self.broadcast(self.form_packet())
