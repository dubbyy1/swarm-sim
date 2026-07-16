# SwarmSim
A 2D Python simulation of a decentralized robot swarm. Robots use IR and UWB for direction to and distance from each other respectively. All other communication is done over WiFi.

![Imgae](/img/swarm-sim.png)

## Features
**Formations:** Robots can form circles and lines, or idle and maintain a minimum distance from their neighbours.
**Signals:** Simulated infrared and Ultra-Wideband signals. IR signals can be blocked by robots or walls. Robots broadcast their IDs over IR and compare signal strengths across their receivers to determine the angle of origin. A simple UWB implementation allows them to broadcast their IDs and determine the precise distance to each other.
**Motion:** The robots use 3-wheel omnidirectional drivetrains for precise movements.
**Communication:** Robots talk over WiFi to build a network/graph representation of the swarm. They use this to find the most efficient paths for formations. Formation commands are broadcast by the controller. The controller can also take over a specific robot and drive it directly.
**Decentralization:** All calculations and decisions are made by the robots themselves. There is no external computer controlling their movements as with most ground swarms.
**UI:** Several variables are exposed, allowing you to control the environment and discover more about the robots' behaviour.

## Installation

Install dependencies:
```sh
pip install -r requirements.txt
```
Run:
```sh
python main.py
```

## Guide
**Controls:**
Click on a robot to select it. 
When remote is toggled, use arrow keys to control selected robot.
When wall is toggled, click 2 points to create a wall between them.

**Info:**
Walls block IR and prevent robots from moving through them. WiFi and UWB aren't affected.
