# torcsRL

Train PyTorch racing agents in TORCS through a Gymnasium environment. This fork
of [raphaelsenn/torcsrl](https://github.com/raphaelsenn/torcsrl) adds a Linux
simulator container, Apple Silicon training, and Tita teacher actions.

<p align="center">
  <img src="./assets/td3_racing_gif.gif" alt="A trained TD3 policy racing on Alpine-1">
</p>

<p align="center"><em>TD3 racing on Alpine-1, from the original project.</em></p>

DDPG, TD3, and SAC have single-step and N-step implementations. TD7 is also
included. The original experiments evaluated DDPG and TD3.

## Quick start

With Docker running, build the simulator, check it, and start a short CPU run:

```bash
sh scripts/container.sh build
sh scripts/container.sh smoke --steps 100
sh scripts/container.sh train --steps 10000
```

Training defaults to Alpine-1 and saves models under `checkpoints/`. The first
build compiles TORCS and takes several minutes.

To watch a native Tita bot, start the desktop:

```bash
sh scripts/container.sh desktop
```

Open [the race viewer](http://127.0.0.1:8000/) and choose a car and track.
Stop the bot race before starting Python training.

[Setup and environment notes](docs/SETUP.md) cover Mac MPS training, Python
examples, teacher collection, and desktop controls.

## Environment

`TorcsSCR-v0` returns 45 observation values and accepts three continuous controls:

| Action index | Control | Range |
| --- | --- | --- |
| 0 | Steering | -1 to 1 |
| 1 | Accelerator | 0 to 1 |
| 2 | Brake | 0 to 1 |

The pedals work independently; Python chooses gears automatically.
`info["action_tita"]` contains the teacher's three controls when the simulator
provides a valid action. Older two-action checkpoints need conversion before
use with this version.

## Original experiments

The GIF, figures, and hyperparameters here come from the upstream project.
DDPG and TD3 each trained for five million steps across three seeds, with
evaluation every 10,000 steps. SAC and TD7 were not evaluated in that study
because compute was limited.

Training used Alpine-1, Aalborg, Street-1, Forza, Wheel-1, and Wheel-2. The held-out
tracks were G-Track-2, Brondehach, and Alpine-2.

<p align="center">
  <img src="./assets/train_val_tracks.png" alt="The six training tracks and three validation tracks">
</p>

<p align="center"><em>Training and validation tracks.</em></p>

<p align="center">
  <img src="./assets/learning_curves.png" alt="DDPG and TD3 learning curves on training and validation tracks">
</p>

<p align="center"><em>DDPG and TD3 learning curves.</em></p>

These experiments have not been rerun with this fork's three-action interface
and pinned teacher build. The quick-start launcher uses its own training
defaults; it does not reproduce the settings below.

### Hyperparameters

| Algorithm | Timesteps | Actor LR | Critic LR | N-Steps | Batch size | Buffer size | Start steps | Discount | Polyak τ | Policy delay | Exploration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DDPG | 5,000,000 | 3e-4 | 3e-4 | 3 | 256 | 1,000,000 | 10,000 | 0.992 | 0.005 | 2 | Gaussian, σ = 0.1 |
| TD3 | 5,000,000 | 3e-4 | 3e-4 | 3 | 256 | 1,000,000 | 10,000 | 0.992 | 0.005 | 2 | Gaussian, σ = 0.1 |

## Further reading

- [Native Tita car baseline](docs/tita-baseline.md)
- [Formula RL: Deep Reinforcement Learning for Autonomous Racing using Telemetry Data](https://arxiv.org/abs/2104.11106)

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

@misc{remonda2021formularl,
      title={Formula RL: Deep Reinforcement Learning for Autonomous Racing using Telemetry Data},
      author={Adrian Remonda and Sarah Krebs and Eduardo Veas and Granit Luzhnica and Roman Kern},
      year={2021},
      eprint={2104.11106},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2104.11106},
}
```
