from dataclasses import dataclass


@dataclass
class Settings:
    reset_swarm_size: int = 0
    reset_emitter_count: int = 3
    reset_receiver_count: int = 16
    collision_iterations: int = 3

    remote_control_enabled: bool = False

    show_components: bool = True
    show_network_lines: bool = True
    show_formation_lines: bool = True
    show_wheel_speeds: bool = True
    show_target_positions: bool = True
    show_ir_range_circle: bool = True
    show_emitter_cones: bool = True

    ir_max_range: float = 400.0
    ir_noise: float = 0.0
    uwb_distance_noise: float = 0.0

    wheel_inaccuracy: float = 0.0

    recency_window: float = 0.5
    network_edge_window: float = 0.5
    ir_top_k: int = 3
    bearing_smoothing: float = 0.35
    distance_smoothing: float = 0.35
    pose_smoothing: float = 0.25
    join_network_cooldown: float = 0.5
    network_report_min_delay: float = 0.0
    network_report_max_delay: float = 0.25
    formation_order_collection_delay: float = 0.35
