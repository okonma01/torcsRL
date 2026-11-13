# Racing-car track tests — 12 November 2026

Historical results from 12 November 2026. The viewer now uses [Tita](tita-baseline.md). The setup and commands below describe an older build.

Question: does any installed track let the GT, stock racer, or Focus beat the open-wheel car with the current Berniw2 profiles?

## Result

No. car1-ow1 was fastest on all 38 installed tracks: 21 road, 9 oval, and 8 dirt/mixed. This holds for the average of laps 2–5, the average of all five laps, and the best single lap. All 152 initial runs completed, giving 760 laps. Six selected tracks were repeated with all four cars: 24 more runs and 120 laps. All repeated lap records match the originals. Total: 176 completed runs and 880 laps.

This is a comparison of the configured Berniw2/car/setup combinations. It does not prove the ranking under another controller, improved setup, physics version, or longer race. The setup was not retuned to create a desired winner.

## Speed and damage

The open-wheel car had nonzero recorded damage on 12 tracks. Brondehach and E-Track-4 had zero recorded lap-end damage for the Focus while all three other cars had nonzero damage. On Spring, only the stock racer had zero recorded lap-end damage. On Dirt-3, the Focus had less damage than the open-wheel car, but remained slower. On Dirt-2, the open-wheel car was both faster and had less recorded damage than the other three cars. These results do not establish a general dirt advantage for the rally car.

Damage can drop after repairs: the Focus on Spring recorded 75, 166, 0, 73, and 149 damage units across five laps. Final damage alone therefore does not show all damage sustained. The table below marks any nonzero lap-end damage, using the maximum recorded value. That value is not total damage and not a count of crashes. Lap-end samples cannot rule out damage repaired within the same lap.

## Full table

Average of laps 2–5, seconds. Lower is faster. An asterisk followed by a number gives the maximum recorded lap-end damage.

| Track | Open-wheel | GT reference | Stock racer | Focus 4WD |
| --- | ---: | ---: | ---: | ---: |
| dirt/dirt-1 | 31.43 | 34.31 *39 | 35.71 *77 | 35.82 *40 |
| dirt/dirt-2 | 80.40 *1064 | 84.88 *2036 | 85.50 *1880 | 86.41 *1954 |
| dirt/dirt-3 | 59.02 *244 | 65.15 *206 | 67.60 *241 | 68.90 *174 |
| dirt/dirt-4 | 66.46 | 77.31 | 82.10 | 83.76 |
| dirt/dirt-5 | 30.39 | 33.04 | 34.43 *15 | 34.20 *3 |
| dirt/dirt-6 | 86.45 | 95.17 | 98.79 | 98.89 |
| dirt/mixed-1 | 44.28 | 46.77 | 48.47 | 47.16 |
| dirt/mixed-2 | 59.04 | 62.98 | 64.90 | 63.51 |
| oval/a-speedway | 21.07 | 28.73 | 32.63 | 35.50 |
| oval/b-speedway | 43.24 | 47.63 | 45.93 *3 | 61.41 |
| oval/c-speedway | 35.47 | 39.23 | 37.90 *3 | 50.31 |
| oval/d-speedway | 37.15 | 40.95 | 39.12 *3 | 52.72 |
| oval/e-speedway | 44.47 | 48.89 | 44.86 *3 | 63.19 |
| oval/e-track-5 | 23.75 | 31.46 | 34.78 | 35.96 |
| oval/f-speedway | 40.24 | 44.29 | 40.76 *3 | 57.15 |
| oval/g-speedway | 32.40 | 35.87 | 37.69 *3 | 45.98 |
| oval/michigan | 28.43 | 36.36 | 38.44 | 42.89 |
| road/aalborg | 67.97 | 76.44 | 78.39 | 80.63 |
| road/alpine-1 | 110.41 | 132.48 | 142.17 | 149.10 |
| road/alpine-2 | 87.09 | 100.39 | 105.93 | 108.56 |
| road/brondehach | 65.47 *95 | 80.81 *3 | 85.41 *60 | 93.35 |
| road/corkscrew | 71.05 | 83.89 | 86.58 | 91.78 *13 |
| road/e-track-1 | 57.73 | 69.62 | 72.21 | 77.31 |
| road/e-track-2 | 100.69 *12 | 119.70 | 132.04 *5 | 140.58 |
| road/e-track-3 | 72.06 | 90.37 | 96.13 | 101.39 |
| road/e-track-4 | 85.42 *152 | 106.45 *55 | 113.89 *42 | 128.47 |
| road/e-track-6 | 73.23 *4 | 88.12 | 90.78 | 98.53 |
| road/eroad | 54.78 *14 | 67.09 | 71.50 | 75.01 |
| road/forza | 75.93 | 90.89 | 90.99 | 106.51 |
| road/g-track-1 | 32.76 | 40.97 | 43.06 | 46.19 |
| road/g-track-2 | 42.06 *6 | 53.55 | 58.25 | 63.24 |
| road/g-track-3 | 53.37 *53 | 64.63 | 68.55 | 71.04 |
| road/ole-road-1 | 99.26 *172 | 116.71 *162 | 119.76 *286 | 133.32 *152 |
| road/ruudskogen | 52.27 *69 | 66.23 | 69.59 | 74.46 |
| road/spring | 372.69 *128 | 445.13 *29 | 475.89 | 512.42 *166 |
| road/street-1 | 67.59 | 80.18 | 82.76 | 89.07 |
| road/wheel-1 | 71.19 | 88.18 | 93.74 | 100.27 |
| road/wheel-2 | 93.86 | 114.47 | 119.75 | 132.19 |

## Method and evidence

- Same Berniw2 compiled driving module for all cars; five solo laps per run.
- car1-ow1 and car1-trb1 use setups ported from Tita; car1-stock1 uses a setup ported from Berniw 1; Focus retains its original Berniw2 setup.
- Fuel use and damage enabled; fresh local settings per run; no car-physics changes.
- All runs were isolated from the active viewer. Its p406 profile was not replaced by this test.
- Repeat tracks: Dirt-2, Dirt-3, Brondehach, E-Track-4, Spring, and E-Speedway.
- Raw logs and race XML: checkpoints/racing-all-tracks-20261112/, checkpoints/racing-track-repeat-20261112/, checkpoints/racing-close-oval-20261112/.
- Summary data: docs/racing-track-test-results-2026-11-12.json.

Run again in a disposable container:

```sh
docker run --rm --network none \
  --mount "type=bind,source=$(pwd),target=/workspace" \
  torcsrl:local python -m scripts.benchmark_tracks \
  --output /workspace/checkpoints/racing-all-tracks-new
```

Add --tracks dirt/dirt-2 oval/e-speedway to select tracks. The script changes driver slot 2 inside its disposable container, so do not run it inside the active viewer.
