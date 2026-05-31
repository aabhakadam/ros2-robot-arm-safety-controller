# ROS2 Robot Arm Safety Controller

A multi-node ROS2 system simulating a 6-DOF collaborative robot arm with real-time force monitoring, autonomous safety-state transitions, and emergency stop logic — built on Ubuntu 24.04 with ROS2 Jazzy.

Collaborative robots (cobots) have one defining safety requirement: they must detect unexpected contact and stop before harming a person. This project implements that safety architecture from first principles.

---

## Industrial context

ISO/TS 15066 defines safety requirements for collaborative robot systems. One core requirement is **force and power limiting** — the robot must transition to a safe state when contact forces exceed defined thresholds. This project implements exactly that:

- `WARNING` state at **15 Nm** → reduce speed
- `DANGER` state at **25 Nm** → emergency stop

These thresholds were chosen based on ISO/TS 15066 guidance for human-robot contact force limits.

---

## System architecture

```
┌─────────────────────┐      /arm/joint_states      ┌──────────────────────┐
│  arm_joint_publisher │ ─────────────────────────► │  force_sensor_node   │
│                     │                             │                      │
│  Simulates 6-DOF arm│                             │  Calculates velocity │
│  joint angles via   │                             │  → estimates force   │
│  sine waves @ 0.5s  │                             │  → injects spikes    │
└─────────────────────┘                             └──────────┬───────────┘
                                                               │
                                              /arm/force_data  │  /arm/safety_status
                                                               │
                                                    ┌──────────▼───────────┐
                                                    │  safety_controller   │
                                                    │                      │
                                                    │  SAFE → NORMAL cmd   │
                                                    │  WARNING → SLOW cmd  │
                                                    │  DANGER → ESTOP      │
                                                    └──────────────────────┘
```

---

## Nodes

| Node | Publishes | Subscribes | Role |
|---|---|---|---|
| `arm_joint_publisher` | `/arm/joint_states` | — | Simulates 6-DOF joint angles via sine waves at different frequencies |
| `force_sensor_node` | `/arm/force_data`, `/arm/safety_status` | `/arm/joint_states` | Estimates force from joint velocity; injects random spikes every 30 messages |
| `safety_controller` | `/arm/command`, `/arm/estop` | `/arm/safety_status` | Evaluates safety state; issues NORMAL/SLOW/STOP commands; tracks statistics |

---

## Topics

| Topic | Type | Content |
|---|---|---|
| `/arm/joint_states` | `Float64MultiArray` | 6 joint angles in degrees (encoder simulation) |
| `/arm/force_data` | `Float64MultiArray` | Force in Newton-metres per joint (torque sensor simulation) |
| `/arm/safety_status` | `String` | SAFE / WARNING / DANGER with joint number and force value |
| `/arm/command` | `String` | NORMAL / SLOW / STOP — commands to motor controllers |
| `/arm/estop` | `String` | Emergency stop signal with cause information |

---

## Key design decisions

**Why callbacks instead of while loops?**
In ROS2, polling with a while loop wastes CPU and introduces latency. Callbacks are registered once — ROS2's executor calls them automatically when a message arrives. `rclpy.spin(node)` hands control to the executor, which manages all timers and subscriptions efficiently. This is how all production robot software is structured.

**Why a deterministic state machine over reactive logic?**
A reactive system (if force > threshold: stop) has no memory of previous states and no audit trail. A deterministic state machine has defined transitions, defined outputs per state, and — crucially — every transition is logged with a timestamp. In safety-critical systems, you must be able to replay exactly what happened and why. I designed the state transitions to be auditable and reproducible across test runs.

**Why ROS2 Jazzy over Humble?**
Humble is supported until 2027; Jazzy until 2029. New projects should use the longer-support release. Jazzy also runs on Ubuntu 24.04, the current LTS, which avoids a future OS migration.

**Why a launch file?**
Without a launch file: 3 terminals, 3 `source` commands, 3 `ros2 run` commands. With a launch file: one command starts the entire system. This is the production deployment standard for ROS2 systems.

---

## How to run

```bash
# Source ROS2 Jazzy
source /opt/ros/jazzy/setup.bash

# Build the workspace
cd ~/ros2_ws
colcon build --packages-select arm_controller

# Source the built workspace
source install/setup.bash

# Launch all three nodes
ros2 launch arm_controller arm_system.launch.py
```

**Inspect the running system (second terminal):**

```bash
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash

ros2 node list                          # see all running nodes
ros2 topic list                         # see all active topics
ros2 topic echo /arm/safety_status      # stream live safety state
ros2 topic hz /arm/force_data           # check sensor publish rate
```

---

## Problems solved during development

**`setup.py` changes not taking effect**
VS Code on Windows saved files with CRLF line endings, silently corrupting the Python config. Fix: write critical config files from the terminal using `cat > file << 'EOF'`, then rebuild with `colcon build`. Lesson: in WSL2, always write config files from the terminal.

**`source install/setup.bash` — the most forgotten command**
After every `colcon build`, you must re-source the workspace. Without it, the terminal cannot find your built packages. Added to `~/.bashrc` to automate this.

**Flood of DANGER messages at launch**
Initially looked like a bug. It was correct behaviour — the simulation ran at 17:53 (evening rush hour), joint velocities were high, force estimates exceeded the 25 Nm DANGER threshold as designed. Lesson: always check whether unexpected output makes sense in context before assuming it is a bug.

---

## What I'd improve with more time

- Replace `arm_joint_publisher` with a hardware interface node reading real encoder data via CAN bus or USB serial — the safety_controller and launch file require zero changes
- Add a ROS2 bag recording to every session for post-hoc analysis
- Implement QoS profiles properly: `RELIABLE` for safety-critical topics (`/arm/estop`), `BEST_EFFORT` for high-frequency sensor streams (`/arm/force_data`)
- Add a Foxglove Studio layout for real-time dashboard visualisation of all five topics

---

## Tech stack

`Python` · `ROS2 Jazzy` · `Ubuntu 24.04 (WSL2)` · `colcon` · `launch files`
