# Mechanical Bull Simulator

A physics-based mechanical bull simulator built with Pygame and Pymunk. This simulation features realistic 2-axis rotation (pitch/roll), stochastic torque functions, G-force calculations, and a breakable rider constraint.

## Features

- **2-Axis Rotation**: The bull platform rotates on both pitch and roll axes around a central pivot point
- **Stochastic Motor**: Realistic bull movement driven by sine wave combinations with random noise
- **Rider Physics**: A physics-based rider object attached to the bull with a breakable constraint
- **G-Force Simulation**: Real-time calculation of gravitational and centripetal forces
- **Constraint Breaking**: Rider falls off when G-forces exceed the threshold (3.0g)
- **Manual Controls**: Keyboard controls to manually tilt the bull and adjust motor intensity
- **Visual Feedback**: Side view visualization with real-time stats display

## Requirements

- Python 3.7+
- Pygame 2.5.0+
- Pymunk 6.6.0+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jesse-dot/Mechanical-Bull-Simulation.git
cd Mechanical-Bull-Simulation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the simulator:
```bash
python mechanical_bull.py
```

## Controls

- **Arrow Keys**: Manually tilt the bull (Left/Right for roll, Up/Down for pitch)
- **+/-**: Adjust motor intensity (0.0x to 3.0x)
- **R**: Reset the simulation
- **ESC**: Quit

## Physics Details

### G-Force Calculation
The simulator calculates G-forces using the formula:
```
G-force = sqrt(centripetal_accel² + gravitational_accel²) / g
```

Where:
- Centripetal acceleration = v² / r (from circular motion)
- Gravitational acceleration = 981 cm/s²
- Default threshold = 3.0g (rider falls off above this)

### Stochastic Torque
The bull's automatic movement is generated using overlapping sine waves with different frequencies plus random noise:
```python
torque = sin(t * freq1) * amplitude * 0.6 + 
         sin(t * freq2) * amplitude * 0.4 + 
         random_noise * amplitude * 0.3
```

### Constraint Breaking
The rider is attached to the bull via a PinJoint constraint with a maximum force limit. When G-forces exceed the threshold, the constraint is removed and the rider falls off.

## Customization

You can modify constants at the top of `mechanical_bull.py`:
- `G_FORCE_THRESHOLD`: Maximum G-force before rider falls (default: 3.0g)
- `BASE_TORQUE`: Manual control torque strength
- `STOCHASTIC_AMPLITUDE`: Automatic movement intensity
- `BULL_MASS`, `RIDER_MASS`: Mass properties
- `FPS`: Simulation frame rate

## License

MIT License