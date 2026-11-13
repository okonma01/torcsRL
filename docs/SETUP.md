# Setup and environment notes

Run commands from the repository root. The [main README](../README.md) has the
Docker quick start and original experiment results.

## Choose where training runs

| Setup | Python and neural networks | TORCS simulator |
| --- | --- | --- |
| Container workflow | Linux container, CPU | Same container |
| Apple Silicon workflow | Native macOS Python, CPU or MPS | Linux container through the local gateway |

The image uses Ubuntu 24.04 and pins the
[SCR simulator](https://github.com/raphaelsenn/torcs-1.3.7) to
`6c451cb779b24dcb42f8f1a20be57dd1d47a8f91`. The Dockerfile includes the build
repairs and GUI patch needed by this setup. On Apple Silicon, use the default
Linux ARM64 image. A native macOS simulator build and Intel Mac setup have not
been verified.

Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/)
or use Colima on macOS:

```bash
brew install docker colima
colima start --cpu 4 --memory 6
```

For a manual Linux build, use the pinned source and build steps in the
[Dockerfile](../Dockerfile). Stock TORCS does not include the required SCR
connection.

## Native Python on Apple Silicon

Use Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m scripts.smoke_test --python-only --device mps
```

Use `--device cpu` if MPS is unavailable. The Python-only check tests a model
action and gradient update without starting TORCS.

Build the image using the main README, then start the simulator gateway:

```bash
sh scripts/container.sh desktop
```

The [viewer](http://127.0.0.1:8000/) shows native bot races and graphical Python
runs. Stop any native bot race before using Python.

```bash
.venv/bin/python -m scripts.smoke_test --device mps \
  --simulator-url http://127.0.0.1:8000 --render --steps 100

.venv/bin/python -m scripts.train --device mps \
  --simulator-url http://127.0.0.1:8000 --render --steps 10000
```

Omit `--render` to run TORCS headlessly. Evaluation uses a separate headless
simulator on SCR port 3002. Python sends actions through local HTTP; SCR's UDP
connection stays inside Linux. The browser display uses software OpenGL. MPS
accelerates the neural networks on the Mac.

## Training options

`scripts/train.py` trains N-step TD3. The older `scripts/main.py` launcher uses
an outdated API.

```bash
sh scripts/container.sh train --track alpine-2 --category road \
  --steps 100000 --seed 1 --telemetry-mode enhanced
```

Use `--warmup`, `--buffer-size`, and `--batch-size` to change collection and
sampling. Warmup must be at least batch size plus three. Models and evaluation
statistics go under `checkpoints/nsteptd3/`. Run `python -m scripts.train --help`
from an installed Python environment for all options.

The launcher trains and evaluates on the chosen track. For a train/validation
split, create separate environments and use `TimedTrackSelectionWrapper` with
`TrackSpec` entries. `HistoryWrapper` can stack observations and past actions.
These wrappers are in [gym_torcs/wrappers.py](../gym_torcs/wrappers.py).

## Python environment

With native Python installed and the gateway running:

```python
import gymnasium as gym
import numpy as np
import gym_torcs  # Registers TorcsSCR-v0.

env = gym.make(
    "TorcsSCR-v0",
    simulator_url="http://127.0.0.1:8000",
    track_name="alpine-2",
    track_category="road",
    telemetry_mode="enhanced",
    observation_noise=False,
)
try:
    obs, info = env.reset()
    action = np.array([0.0, 0.3, 0.0], dtype=np.float32)
    obs, reward, terminated, truncated, info = env.step(action)
finally:
    env.close()
```

`render_mode="human"` opens the race in the viewer. Leaving out `simulator_url`
uses a local Linux TORCS installation instead of the gateway. Each environment
needs a different SCR port: 3001 through 3010.

The 45 observation values include speed, acceleration, RPM, heading, track
position, track distances, wheel speeds, racing-line error, and lookahead
curvature. They are normalized and clipped to [-1, 1]. Observation noise is on
by default. The action is `[steering, accelerator, brake]`, with bounds
`[-1, 0, 0]` to `[1, 1, 1]`. The environment clips each control to its range and
rejects wrong shapes or non-finite values. Gear changes are automatic.

Reward is normalized forward speed multiplied by closeness to the reference
line. Damage, leaving the track, facing backward, or low speed after the
startup allowance give a penalty and end the episode. A completed lap truncates
it by default;
`truncate_on_successful_lap=False` allows further laps. The step limit also
truncates an episode. See [gym_torcs/env.py](../gym_torcs/env.py) for exact rules.

## Teacher actions and replay

The pinned simulator uses Tita's planner and adapted driving logic to compute
`titaSteer`, `titaGas`, and `titaBrake` for the current car state. It sends them
before receiving Python's next command. Python exposes them separately in
`info["action_tita"]`. It still chooses gears; the teacher does not supply the
full native bot's clutch, gear, and recovery behavior.

To store a teacher transition, keep the `env.reset()` line in the Python
example above and replace its fixed action and `env.step()` lines with this
code, inside the `try` block before `env.close()`:

```python
from torcsrl.buffers.replay_buffer import ReplayBuffer

replay_buffer = ReplayBuffer(
    obs_dim=45, action_dim=3, capacity=10000, batch_size=256,
)
action = info["action_tita"]
if action is None:
    raise RuntimeError("The simulator did not provide a valid teacher action.")
next_obs, reward, terminated, truncated, next_info = env.step(action)
replay_buffer.push(obs, action, reward, next_obs, terminated)
```

For further transitions, use `next_obs` and `next_info`; reset on either
`terminated` or `truncated`. The replay buffer's terminal flag is separate from
the episode boundary. Save truncation and episode boundaries as well if you
keep trajectories on disk.

`DDPG.train()` starts with `collect_expert_rollouts()`. The N-step TD3 launcher
uses random warmup actions. Three-action teacher collection and a short DDPG
training run have passed live checks. Teacher-controlled full laps also passed
on Michigan and Forza with headless training settings. These checks do not
establish the performance shown in the original learning curves.

### Telemetry modes

The environment defaults to `enhanced`, which requires the teacher,
acceleration, and lookahead fields. The command-line launchers explicitly use
`standard` by default for older simulators. Standard mode keeps fields that
are present and fills missing acceleration/lookahead values with zeros. It
uses the track center when the teacher line is missing. A missing or invalid
teacher action is `None`, so expert collection needs a simulator with valid
teacher fields in either mode.

Racing-line CSVs are optional and are not included. Paths in
[gym_torcs/constants.py](../gym_torcs/constants.py) can provide lookahead
curvature in either mode.

### Moving from two actions to three

The actor now outputs steering and two independent pedals. DDPG keeps `Tanh`
and scales its outputs with the existing fixed `action_scale` and `action_bias`
buffers. Critics and replay buffers take the action dimension from the
environment. Old two-action checkpoints and replay data need conversion or a
fresh run. The tutorial logs pedal columns to `tutorial/runs_three_actions.csv`
so it does not append a new schema to `runs.csv`.

## Desktop and native bots

The viewer offers Tita's four original rear-wheel-drive TRB1 cars, with their
installed setups and physics. Choose a car, track, lap count, and camera, then
press **Start race**. Camera changes take effect on the next start.
[Baseline results](tita-baseline.md) cover five-lap native runs across all
38 installed tracks. Lap-end damage samples can drop after repairs; they are
not a count of crashes or total damage.

Native benchmarks keep fuel use and damage enabled. Headless Gym runs use
`-nofuel -nodamage -nolaptime`; graphical runs launch with different flags.
Keep race conditions equal when comparing times.

`desktop` reuses an existing container. After rebuilding, replace it to load
the new image:

```bash
sh scripts/container.sh desktop-stop
sh scripts/container.sh desktop
```

`desktop-stop` also ends the gateway and any races it owns. For logs:

```bash
sh scripts/container.sh desktop-logs
```

To watch the simple centerline controller from native Python:

```bash
.venv/bin/python -m scripts.watch --seconds 120
```

Leave out `--seconds` to run until Ctrl+C. Run one graphical training or demo
command at a time. A race closes when its command finishes; the desktop stays
available. If a killed learner leaves a session behind, restart the desktop.
The display is 1280 x 800 and supports full screen. Mouse and keyboard input
control TORCS menus and cameras.

The viewer and noVNC ports, 8000 and 6080, bind to localhost. The viewer has no
password and is intended for local use. Colima users can stop the VM with
`colima stop`, which also stops other containers in that VM.

## Tests

Install pytest in the native environment, then run the suite:

```bash
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest -q
```

The Docker smoke check also runs a real SCR race and a TD3 gradient update:

```bash
sh scripts/container.sh smoke --steps 100
```
