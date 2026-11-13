# Berniw and Berniw2 comparison

Historical results from 12 November 2026. The viewer now uses [Tita](tita-baseline.md). The setup and commands below describe an older build.

Installed Berniw3 entries are all rear-wheel drive. Berniw2 has six four-wheel-drive rally entries.

Compared Berniw and Berniw2 using every car model shared by their installed entries: car4-trb1, car5-trb1, car7-trb1, and car1-trb3. Each driver ran five solo laps on Alpine-2, Forza, Michigan, and Dirt-4, with fresh local settings, default driver setups, fuel use, and damage enabled.

All 32 runs completed. All lap times, recorded top speeds, and damage values matched exactly within the 16 paired conditions. Four main helper source files also match after comments and whitespace are removed: mycar.cpp, pathfinder.cpp, trackdesc.cpp, and spline.cpp. Shared-car default setup values match. This is evidence of matching performance in these conditions, not proof for every track, car, or traffic situation.

## Selected four-car group

- car1-ow1: light open-wheel rear-wheel-drive car; retained.
- p406: heavy front-wheel-drive car; retained.
- car1-trb1: original rear-wheel-drive reference car; retained.
- pw-focuswrc: four-wheel-drive rally car; replaces car1-trb3.

Berniw2 is the selected baseline module. The four-car profiles have now been configured and verified: see [setup and test results](berniw2-baseline.md). The comparison above used the original, unmodified shared-car entries.

Raw logs, race XML and per-lap records: checkpoints/berniw-family-20261112/.
