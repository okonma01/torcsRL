# torcsRL

This repo provides a modern PyTorch implementation/interface for training RL agents in TORCS. It uses a Gymnasium environment interface and provides configurable training and evaluation tracks.

<p align="center">
  <img src="./assets/td3_racing_gif.gif">
</p>

<p align="center"> <em>Gif: Trained TD3 policy racing on Alpine-1.</em> </p>

## Implemented Algoritms

* DDPG (N-Step)
* TD3 (N-Step)
* SAC (N-Step; Not evaluated yet - due to limited compute)
* TD7 (Not evaluated yet - due to limited compute )

## Experiment

Note that due to my limited compute resources, I evaluated only two algorithms: DDPG and TD3. Each algorithm was trained on the six training tracks and evaluated on the three validation tracks every 10,000 timesteps. Each algorithm was trained for 5 million timesteps and evaluated across three different seeds.

#### Training and Validation Tracks

<p align="center">
  <img src="./assets/train_val_tracks.png">
</p>

<p align="center"> <em>Figure 1: Training and validation tracks. Alpine-1, Aalborg, Street-1, Forza, Wheel-1, and Wheel-2 are used for training, while G-Track-2, Brondehach, and Alpine-2 are used for validation.</em> </p>

<p align="center">
  <img src="./assets/learning_curves.png">
</p>

<p align="center"> <em>Figure 2: Learning curves of DDPG and TD3 on training and validation tracks. </em> </p>

#### Results

#### Hyperparameters

| Algorithm | Timesteps | Actor LR | Critic LR | N-Steps | Batch size | Buffer size | Start steps | Discount | Polyak τ | Policy delay | Exploration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DDPG | 5,000,000 | 3e-4 | 3e-4 | 3 | 256 | 1,000,000 | 10,000 | 0.992 | 0.005 | 2 | Gaussian, σ = 0.1 |
| TD3 | 5,000,000 | 3e-4 | 3e-4 | 3 | 256 | 1,000,000 | 10,000 | 0.992 | 0.005 | 2 | Gaussian, σ = 0.1 |


## Environment reference and first research project

See the [local TORCSRL guide](docs/torcsrl-guide/README.md) for observation and
action spaces, rewards, dashboard indicators, setup examples, capability limits,
and a scoped reward-design experiment for autonomous racing.

## Usage

```python
import gymnasium as gym
import gym_torcs

from torcsrl import NStepTD3
from gym_torcs.wrappers import TimedTrackSelectionWrapper, TrackSpec, HistoryWrapper


train_tracks = [
    TrackSpec("alpine-1", "road"),
    TrackSpec("aalborg", "road"),
    TrackSpec("street-1", "road"),
    TrackSpec("forza", "road"),
    TrackSpec("wheel-1", "road"),
    TrackSpec("wheel-2", "road"),
]

val_tracks = [
    # Training tracks
    TrackSpec("alpine-1", "road"),
    TrackSpec("aalborg", "road"),
    TrackSpec("street-1", "road"),
    TrackSpec("forza", "road"),
    TrackSpec("wheel-1", "road"),
    TrackSpec("wheel-2", "road"),

    # Validation tracks
    TrackSpec("g-track-1", "road"),
    TrackSpec("g-track-2", "road"),
    TrackSpec("brondehach", "road"),
    TrackSpec("alpine-2", "road"),
]


SEED = 0
HORIZON_OBS = 3
HORIZON_ACT = 3
SWITCH_TRACK_EVERY = 50_000

train_env = gym.make(
    "TorcsSCR-v0",
    render_mode=None,
    port=3001,
    race_type="practice",
    track_name="alpine-1",
    track_category="road",
    reset_strategy="relaunch",
    telemetry_mode="standard",
)
train_env = TimedTrackSelectionWrapper(
    train_env, tracks=train_tracks, switch_every_steps=SWITCH_TRACK_EVERY,
)
train_env = HistoryWrapper(train_env, HORIZON_OBS, HORIZON_ACT)


val_env = gym.make(
    "TorcsSCR-v0",
    render_mode=None,
    port=3002,
    race_type="practice",
    track_name="alpine-2",
    track_category="road",
    reset_strategy="relaunch",
    telemetry_mode="standard",
)
val_env = HistoryWrapper(val_env, HORIZON_OBS, HORIZON_ACT)
val_env = TimedTrackSelectionWrapper(
    val_env, val_tracks, switch_every_steps=1
)

alg = NStepTD3(
    train_env,
    val_env,
    ac_kwargs={},
    n_steps=3,
    lr_actor=3e-4,
    lr_critic=3e-4,
    buffer_size=3_000_000,
    buffer_start_size=25_000,
    batch_size=256,
    tau_polyak=0.005,
    save_every=10_000,
    eval_every=10_000,
    device="cpu",  # use "mps" for native macOS Python, "cuda" for NVIDIA
    seed=SEED,
)

alg.train(5_000_000)
```

## Install

### macOS (Apple Silicon)

The Python library runs natively on Apple Silicon with Python 3.12, including
PyTorch's Metal (`mps`) backend. The SCR-patched TORCS simulator is a separate
dependency: its build uses X11/GLX, PLIB, and Linux launch scripts. A native macOS
simulator build is not currently verified.

For a complete headless setup, run Python and the simulator together in a Linux
container. The Dockerfile builds the exact SCR fork required by this environment,
pinned to commit `6c451cb779b24dcb42f8f1a20be57dd1d47a8f91`. On Apple Silicon,
Docker selects Linux ARM64 automatically; do not force `linux/amd64`.

Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/)
or use Homebrew with Colima:

```bash
brew install docker colima
colima start --cpu 4 --memory 6
```

From this repository:

```bash
sh scripts/container.sh build
sh scripts/container.sh smoke --steps 100
sh scripts/container.sh train --steps 10000
```

The smoke test checks package imports, a TD3 action and gradient update, then
starts a real SCR race and checks observations for 100 steps. Training defaults
to Alpine-1, uses CPU inside the container, and writes models and evaluation
statistics to the host's `checkpoints/` folder. Customize a run with:

```bash
sh scripts/container.sh train --track alpine-2 --steps 100000 --seed 1
```

**Telemetry compatibility:** the pinned simulator now includes Tita teacher
steering, accelerator, and brake fields, plus acceleration and lookahead
curvature. `info["action_tita"]` exposes the teacher action as
`[titaSteer, titaGas - titaBrake]`; the Python environment still chooses gears.
These values use Tita's planner and adapted driving logic, rather than recording
the complete native Tita controller. Use `--telemetry-mode enhanced` for training
that requires these fields. This does not establish equivalence to the enhanced
observations/reward used in the published experiments.

The launchers continue to select `telemetry_mode="standard"` for compatibility
with older simulators. Standard mode preserves teacher fields when supplied,
zeroes unavailable acceleration/lookahead channels, and uses the track center
when no teacher line is supplied. `info["action_tita"]` is `None` if any teacher
action field is missing. Both modes retain the 45-element observation layout;
optional racing-line CSVs can supply lookahead curvature in either mode.

After rebuilding, replace an existing desktop container with
`sh scripts/container.sh desktop-stop` followed by
`sh scripts/container.sh desktop` to load the new simulator.

The initial image build downloads and compiles the simulator and can take several
minutes. Headless container training needs no published network ports. Stop
Colima when finished with `colima stop` (this also stops other containers in that
VM). Intel Macs are not part of the verified macOS setup.

To use just the Python library on macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m scripts.smoke_test --python-only --device mps
```

Use `--device cpu` if Metal is unavailable. The Python-only test does not need
TORCS.
Use `scripts/train.py` for the current API; the older `scripts/main.py` launcher
is outdated. Racing-line CSVs are optional and are not included in this repo;
standard mode uses zero curvature when neither CSV nor simulator curvature is
available.

#### Native MPS training and a browser race view

Build the image above, install the native Python dependencies, then start the
simulator gateway and virtual desktop once:

```bash
sh scripts/container.sh desktop
```

Running `desktop` again reuses the existing running container, or starts it if
stopped. After rebuilding the image, run `desktop-stop` followed by `desktop`
to replace the existing container and use the new image.

Open [the race viewer](http://127.0.0.1:8000/).
Choose a **Car**, **Track**, number of **Laps**, and **View**, then press
**Start race**. Tita drives four native TRB1 racing cars: `car1-trb1`,
`car2-trb1`, `car3-trb1`, and `car4-trb1`. All four are rear-wheel drive and
use their original installed Tita entries and setups. There are no open-wheel,
FWD, or 4WD choices in this baseline. The image validates these native profiles
without changing their settings or the car physics.

Choose another car and press **Start race** again to switch. **Stop race** ends
the current run. **Follow car** keeps a steady view behind the car; **Bonnet**
and **Overhead** are also available. Camera choices take effect when starting
a race. The table above the race shows five-lap results, and the selected-car
summary covers every installed track. Damage is reported from lap-end samples;
repairs can reduce it, so the highest sampled value is shown.

Use the same car and track when comparing Tita with an RL agent. The viewer
does not yet export trajectories. See [the Tita baseline](docs/tita-baseline.md).
The earlier Berniw2 and single-car bot comparisons are historical test records.

The viewer shows a clear idle message when no race is running.
**Full screen** enlarges the race to your browser's full
screen; press Escape to return. TORCS renders at 1280 x 800, fills the virtual
display, and scales to fit the browser window.

The viewer uses noVNC, a browser client for the Linux simulator's display. It
does not change where training runs: MPS training still runs on your Mac.

Stop the bot race before training. This command trains on the
Mac's Metal GPU and shows its training race in the viewer:

```bash
.venv/bin/python -m scripts.train --device mps \
  --simulator-url http://127.0.0.1:8000 --render --steps 10000
```

Omit `--render` for faster headless simulator operation while keeping MPS
training. Evaluation uses a separate headless simulator on SCR port 3002. The
gateway forwards telemetry/actions over local HTTP; SCR's UDP traffic stays
inside Linux. This works without UDP port forwarding in Colima. Rendering uses
Mesa software OpenGL inside Linux; MPS accelerates the native neural networks.
The simulator and browser desktop do not use Metal.

To verify the complete split setup without a long run:

```bash
.venv/bin/python -m scripts.smoke_test --device mps \
  --simulator-url http://127.0.0.1:8000 --render --steps 100
```

To watch a simple driving demo instead of training:

```bash
.venv/bin/python -m scripts.watch --seconds 120
```

Without `--seconds`, the command-line demo runs until Ctrl+C. The demo follows
the track center with a basic controller, not a trained agent.
Run one training/demo command at a time; session ownership prevents a second run
from interrupting an active race. A GUI race closes when its command finishes;
the desktop stays available. The container patches TORCS to start graphical
races directly from their generated configuration, avoiding menu-key timing
failures on reset. Graphical resets still relaunch TORCS and are slower than
headless resets. Keyboard and mouse
input in the viewer controls TORCS menus/cameras, not the agent's driving actions.

Stop the desktop and gateway with:

```bash
sh scripts/container.sh desktop-stop
```

Ports 6080 (display transport) and 8000 (viewer and gateway) are published only on `127.0.0.1`. The
viewer has no password and is intended for local use. Do not expose those ports
on a public interface. For gateway diagnostics, run
`sh scripts/container.sh desktop-logs`. If a learner is forcibly killed before
cleanup, restart the desktop to release its session before beginning another run.

### Ubuntu 26.04

#### Install TORCS 1.3.7 with the SCR server patch

1. Clone the TORCS repository:

```bash
git clone https://github.com/raphaelsenn/torcs-1.3.7
```

2. Enter the repository:

```bash
cd torcs-1.3.7
```

3. Install the required packages:

```bash
sudo apt install -y \
    libglib2.0-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    freeglut3-dev \
    libplib-dev \
    libopenal-dev \
    libalut-dev \
    libxi-dev \
    libxmu-dev \
    libxrender-dev \
    libxrandr-dev \
    libpng-dev \
    libvorbis-dev \
    gcc \
    g++ \
    make \
    cmake \
    automake \
    autoconf \
    libtool \
    libxxf86vm-dev \
    xautomation
```

4. Build and install TORCS:

```bash
make
sudo make install
sudo make datainstall
```

#### Install `torcsrl`

1. Clone the repository:

```bash
git clone https://github.com/raphaelsenn/torcsrl
```

2. Enter the repository:

```bash
cd torcsrl
```

3. Create and activate a conda environment:

```bash
conda create -n torcsrl python=3.11 -y
conda activate torcsrl
```

4. Install the Python requirements:

```bash
pip install -r requirements.txt
```

5. Install `torcsrl` in editable mode:

```bash
pip install -e .
```

### Fedora Linux 44 Workstation

#### Install TORCS 1.3.7 with the SCR server patch

1. Clone the TORCS repository:

```bash
git clone https://github.com/raphaelsenn/torcs-1.3.7
```

2. Enter the repository:

```bash
cd torcs-1.3.7
```

3. Install the required packages:

```bash
sudo dnf install \
  glib2-devel \
  mesa-libGL-devel \
  mesa-libGLU-devel \
  freeglut-devel \
  plib-devel \
  openal-soft-devel \
  freealut-devel \
  libXi-devel \
  libXmu-devel \
  libXrender-devel \
  libXrandr-devel \
  libpng-devel \
  libvorbis-devel \
  gcc \
  gcc-c++ \
  make \
  cmake \
  automake \
  autoconf \
  libtool \
  libXxf86vm-devel \
  xautomation
```

4. Build and install TORCS:

```bash
make
sudo make install
sudo make datainstall
```

You should now be able to start TORCS with:

```bash
sudo torcs
```

#### Install `torcsrl`

1. Clone the repository:

```bash
git clone https://github.com/raphaelsenn/torcsrl
```

2. Enter the repository:

```bash
cd torcsrl
```

3. Create and activate a conda environment:

```bash
conda create -n torcsrl python=3.11 -y
conda activate torcsrl
```

4. Install the Python requirements:

```bash
pip install -r requirements.txt
```

5. Install `torcsrl` in editable mode:

```bash
pip install -e .
```

## Citations

```bibtex
@misc{lillicrap2019continuouscontroldeepreinforcement,
      title={Continuous control with deep reinforcement learning}, 
      author={Timothy P. Lillicrap and Jonathan J. Hunt and Alexander Pritzel and Nicolas Heess and Tom Erez and Yuval Tassa and David Silver and Daan Wierstra},
      year={2019},
      eprint={1509.02971},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/1509.02971}, 
}

@misc{fujimoto2018addressingfunctionapproximationerror,
      title={Addressing Function Approximation Error in Actor-Critic Methods}, 
      author={Scott Fujimoto and Herke van Hoof and David Meger},
      year={2018},
      eprint={1802.09477},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/1802.09477}, 
}

@misc{haarnoja2018softactorcriticoffpolicymaximum,
      title={Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor}, 
      author={Tuomas Haarnoja and Aurick Zhou and Pieter Abbeel and Sergey Levine},
      year={2018},
      eprint={1801.01290},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/1801.01290}, 
}


@misc{fujimoto2023salestateactionrepresentationlearning,
      title={For SALE: State-Action Representation Learning for Deep Reinforcement Learning}, 
      author={Scott Fujimoto and Wei-Di Chang and Edward J. Smith and Shixiang Shane Gu and Doina Precup and David Meger},
      year={2023},
      eprint={2306.02451},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2306.02451}, 
}
```
