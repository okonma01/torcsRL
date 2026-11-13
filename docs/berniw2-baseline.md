# Four-car Berniw2 baseline

Historical results from 12 November 2026. The viewer now uses [Tita](tita-baseline.md). The setup and commands below describe an older build.

Configured and verified on 12 November 2026. The simulator image installs the four profiles automatically. The active viewer offers cars rather than different bot modules.

| Driver slot | Car | Setup source |
| --- | --- | --- |
| berniw2:4 | car1-ow1 | Tita 1 |
| berniw2:2 | p406 | Tita 2 |
| berniw2:3 | car1-trb1 | Tita 3 |
| berniw2:1 | pw-focuswrc | Original Berniw2 1 |

The compiled driver remains Berniw2. For the three new cars, all car-specific setup files and textures are copied from their working Tita entries. Old rally-car overrides are removed from the reused slots. No car physics files or driving code are changed. Driver names remain the names registered by the compiled module. Slots 2–4 replace their previous rally-car assignments; the original definitions and profile folders are backed up in the simulator data under drivers/.torcsrl-original-berniw2. Slots 5–10 remain as supplied.

## Five-lap checks

Five solo laps for each car on each track: 16 completed runs, 80 laps, zero damage in every run. Fresh local settings per run; fuel use and damage enabled. These are compatibility checks, not optimised setups or proof for every track. Averages below exclude the standing-start first lap.

| Car | Alpine-2 | Forza | Michigan | Dirt-4 |
| --- | ---: | ---: | ---: | ---: |
| car1-ow1 | 87.09 | 75.93 | 28.43 | 66.46 |
| p406 | 128.07 | 122.83 | 50.62 | 99.66 |
| car1-trb1 | 100.39 | 90.89 | 36.36 | 77.31 |
| pw-focuswrc | 108.56 | 106.51 | 42.89 | 83.76 |

Measurements: scripts/baseline_results.json. Raw race XML and logs: checkpoints/berniw2-baseline-20261112/.

## Run again

```sh
docker run --rm --network none \
  --mount "type=bind,source=$(pwd),target=/workspace" \
  torcsrl:local python -m scripts.benchmark_bots --baseline \
  --output /workspace/checkpoints/berniw2-baseline-new --laps 5
```

The Gym/SCR training environment still controls its own driver. Adding multi-car RL training is separate from these native baseline profiles.
