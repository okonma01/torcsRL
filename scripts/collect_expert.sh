#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

# Start the gateway first: sh scripts/container.sh desktop
# Edit these defaults, or override them: STEPS=500 sh scripts/collect_expert.sh
STEPS=5_000                 # Saved decisions, not simulator steps.
ACTION_REPEAT=4     # Hold each teacher action for this many steps.
TRACK=forza              # Track name installed in TORCS.
CATEGORY=road           # Track category: road, oval, or dirt.
SEED=0                      # Random seed.
SIMULATOR_URL=http://127.0.0.1:8000

# Existing output files are protected; change the path for a new collection.
OUTPUT=${OUTPUT:-datasets/expert/${TRACK}-repeat${ACTION_REPEAT}-seed${SEED}.npz}

# Extra CLI options override defaults. Add --render to show the race.
exec .venv/bin/python -m scripts.collect_expert \
  --steps "$STEPS" \
  --action-repeat "$ACTION_REPEAT" \
  --track "$TRACK" \
  --category "$CATEGORY" \
  --seed "$SEED" \
  --simulator-url "$SIMULATOR_URL" \
  --output "$OUTPUT" \
  "$@"
