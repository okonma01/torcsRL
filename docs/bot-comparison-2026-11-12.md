# Native bot comparison — 12 November 2026

Historical results from 12 November 2026. The viewer now uses [Tita](tita-baseline.md). The setup and commands below describe an older build.

The viewer now offers four choices: berniw 3, Olethros 3, tita 3, and bt 3. These cover the four different sets of solo results found in this test.

## Results

Average time for laps 2 to 5, in seconds. Lower is faster. The first lap starts from rest, so it is left out of this average. All six tested bots finished every run. An asterisk means the car took damage during the five-lap run.

| Bot | Alpine-2 | Forza | Michigan | Dirt-4 |
| --- | ---: | ---: | ---: | ---: |
| berniw 3 | 100.22 | 90.91 | 36.40 | 77.48 |
| Olethros 3 | 99.86 * | 89.43 | 37.38 | 77.41 |
| tita 3 | 100.25 | 90.83 | 36.41 | 77.24 |
| bt 3 | 101.57 * | 93.73 | 37.08 | 82.60 |
| inferno 3 | 100.25 | 90.83 | 36.41 | 77.24 |
| lliaw 3 | 100.25 | 90.83 | 36.41 | 77.24 |

On Alpine-2, Olethros was fastest on average but ended with 503 damage units. Berniw was fastest among the runs with no damage. BT ended with 15 damage units. All other runs on all four tracks ended with zero damage. Damage is a simulator value, not a count of crashes.

On Forza, Olethros had the fastest average without damage. On Michigan, Berniw had the fastest average; BT had the fastest single lap (36.30 seconds), but a slower average. On Dirt-4, Tita, Inferno, and Lliaw tied for the fastest average.

Tita, Inferno, and Lliaw produced identical times, speeds, and damage values on every lap in all four tracks. Their pinned source has the same driving logic apart from module names and file paths; their installed car1-trb1 setup XML also matches. This supports keeping just Tita in the solo viewer. It does not prove that every car, track, or traffic situation will match.

BT improved its Alpine-2 lap time from 110.34 seconds on lap 1 to 99.85 seconds on lap 5. It remains as the fourth choice for comparison, even though its average was slower in these short runs.

## Test conditions

- TORCS source revision: `8134c27be99bc2039f51fd821129e1ddf7514f64`, with this project’s GUI patch.
- Same car model: `car1-trb1`. Each bot kept its own default setup and fuel choice.
- Solo practice: five laps per bot, six bots, four tracks. No traffic.
- Fuel use and damage stayed enabled; no training-mode flags were used.
- A fresh local settings folder was used for each run. Previous learned settings were not reused.
- Runs used the headless simulator. Times come from TORCS simulation time, not wall-clock time or browser FPS.
- Two independent rounds completed: 48 runs and 240 laps. Every lap record matched between rounds.
- These are short solo comparisons for this build. They do not measure overtaking or long-race performance. Untested tracks have no claimed winner.

## Evidence and rerunning

Raw race XML, logs, and lap records are in `checkpoints/bot-benchmark-20261112/full/` and `checkpoints/bot-benchmark-20261112/repeat/`. The initial BT check is in the parent folder. A copy of the measurements used by the viewer is in `scripts/bot_comparison.json`.

To run another round from the repository root with Docker running:

```sh
docker run --rm --network none \
  --mount "type=bind,source=$(pwd),target=/workspace" \
  torcsrl:local python -m scripts.benchmark_bots \
  --output /workspace/checkpoints/bot-benchmark-new --laps 5
```

Add `--tracks road/alpine-2` to test only that track. The script saves results; it does not change the viewer shortlist automatically.

Published comparisons provide context but do not rank this exact build. For example, [Koutník et al., Evolving Large-Scale Neural Networks for Vision-Based TORCS](https://people.idsia.ch/~juergen/fdg2013.pdf) compares built-in bots on a custom track using distance and top speed. Those results are not five-lap times for these tracks.
