# Native Tita RWD baseline

The active viewer uses Tita with four original rear-wheel-drive TRB1 racing cars. Open-wheel, FWD, and 4WD choices have been removed from the viewer baseline.

| Native entry | Car |
| --- | --- |
| Tita 3 | car1-trb1 |
| Tita 4 | car2-trb1 |
| Tita 5 | car3-trb1 |
| Tita 6 | car4-trb1 |

All four have a base mass of 1,150 kg before fuel and belong to the same racing class. Differences in engine curves, balance, aerodynamics, and setups remain. No setups were ported, and no driving code or car physics was modified. The image validates the existing definitions without rewriting them.

## Verification

Five solo laps per car on all 38 installed tracks: 152 completed runs, 760 laps. Tita uses stock car-specific setups; fuel use and damage are enabled; each run starts with fresh local settings. Average times below exclude the standing-start first lap.

The fastest-to-slowest time spread was at most 3% on 36 of 38 tracks. The largest spread was 9.27% on dirt/dirt-2. Wins by average of laps 2–5: car3-trb1: 17, car4-trb1: 21.

These results support a closer performance group, not identical cars or equal performance on every track. Damage still occurs on some tracks. Peak lap-end damage is a sampled value, not total damage or a crash count; pit repairs can reduce damage between samples.

| Track | car1-trb1 | car2-trb1 | car3-trb1 | car4-trb1 |
| --- | ---: | ---: | ---: | ---: |
| dirt/dirt-1 | 34.30 * | 33.99 * | 33.90 * | 34.09 * |
| dirt/dirt-2 | 84.33 * | 88.58 * | 83.26 * | 90.98 * |
| dirt/dirt-3 | 65.17 * | 64.49 * | 64.30 * | 64.55 * |
| dirt/dirt-4 | 77.24 | 76.39 | 76.13 | 76.18 |
| dirt/dirt-5 | 33.04 | 32.73 | 32.58 | 32.76 * |
| dirt/dirt-6 | 95.19 | 94.08 | 94.00 | 94.29 |
| dirt/mixed-1 | 46.78 | 46.63 | 46.24 | 46.58 |
| dirt/mixed-2 | 62.92 | 62.73 | 62.12 | 62.54 |
| oval/a-speedway | 28.77 | 28.10 | 27.59 | 27.64 * |
| oval/b-speedway | 47.63 | 47.07 * | 46.91 * | 46.44 * |
| oval/c-speedway | 39.23 | 38.71 * | 38.65 * | 38.23 * |
| oval/d-speedway | 40.95 | 40.46 * | 40.34 * | 39.92 * |
| oval/e-speedway | 48.89 | 48.37 * | 48.14 * | 47.66 * |
| oval/e-track-5 | 31.42 | 31.05 | 30.55 | 30.67 |
| oval/f-speedway | 44.29 | 43.80 * | 43.62 * | 43.17 * |
| oval/g-speedway | 35.86 | 35.37 * | 35.34 * | 34.95 * |
| oval/michigan | 36.41 | 36.01 | 35.82 | 35.53 |
| road/aalborg | 76.37 | 76.12 | 76.04 | 76.09 |
| road/alpine-1 | 132.35 | 131.68 | 131.47 | 130.95 |
| road/alpine-2 | 100.25 | 99.83 | 99.16 | 99.59 |
| road/brondehach | 80.64 * | 80.42 * | 79.46 * | 79.65 * |
| road/corkscrew | 83.90 | 83.54 * | 83.25 * | 83.19 * |
| road/e-track-1 | 69.59 | 69.27 * | 68.96 | 68.82 |
| road/e-track-2 | 119.64 | 118.95 | 118.34 * | 118.17 * |
| road/e-track-3 | 87.59 | 86.86 | 86.25 | 86.66 |
| road/e-track-4 | 106.38 * | 104.64 * | 104.10 * | 103.64 * |
| road/e-track-6 | 87.99 | 87.64 | 87.54 | 87.01 * |
| road/eroad | 67.07 | 66.70 | 66.11 | 66.14 * |
| road/forza | 90.83 | 90.34 | 90.43 | 89.35 |
| road/g-track-1 | 40.98 | 40.66 | 40.43 | 40.26 |
| road/g-track-2 | 53.44 | 52.90 | 52.49 * | 52.22 * |
| road/g-track-3 | 64.57 | 64.19 * | 63.57 * | 63.70 * |
| road/ole-road-1 | 116.69 * | 116.19 * | 115.78 * | 115.36 * |
| road/ruudskogen | 65.96 | 65.55 * | 64.87 * | 64.97 * |
| road/spring | 444.62 * | 442.18 * | 440.25 * | 439.94 * |
| road/street-1 | 80.14 | 79.96 | 79.88 | 79.63 |
| road/wheel-1 | 88.07 | 87.58 | 87.11 | 86.85 |
| road/wheel-2 | 114.35 | 113.61 | 113.36 | 112.75 * |

An asterisk means nonzero recorded lap-end damage. Raw logs and race XML: checkpoints/tita-rwd-baseline-20261112/. Viewer data: scripts/baseline_results.json.

## Running

Open http://127.0.0.1:8000/ and select a car, track, laps, and camera. The steady follow camera is the default. Stop the native race before starting a Python training run.

For headless tests inside the simulator image, run python -m scripts.benchmark_bots --baseline --output /workspace/checkpoints/tita-test. Add --tracks with installed category/name pairs to choose tracks.

The SCR/Gym training environment still controls its own driver. This change configures the native reference baseline, not multi-car RL training.
