#!/bin/sh
# Works with Docker Desktop or Colima, including an unlinked Homebrew Docker CLI.
set -eu
cd "$(dirname "$0")/.."
if command -v docker >/dev/null 2>&1; then
    docker_cli=$(command -v docker)
elif command -v brew >/dev/null 2>&1 && [ -x "$(brew --prefix docker)/bin/docker" ]; then
    docker_cli="$(brew --prefix docker)/bin/docker"
else
    echo "Docker CLI missing. Install Docker Desktop or: brew install docker colima" >&2
    exit 1
fi
if ! "$docker_cli" info >/dev/null 2>&1; then
    echo "Docker engine unavailable. Start Docker Desktop or run: colima start --cpu 4 --memory 6" >&2
    exit 1
fi
image=${TORCSRL_IMAGE:-torcsrl:local}
operation=${1:-smoke}
if [ "$#" -gt 0 ]; then shift; fi
desktop_exists() {
    desktop_name=$("$docker_cli" container ls -a --filter 'name=^/torcsrl-desktop$' --format '{{.Names}}') || exit "$?"
    [ "$desktop_name" = "torcsrl-desktop" ]
}
case "$operation" in
    build) exec "$docker_cli" build -t "$image" "$@" . ;;
    smoke) exec "$docker_cli" run --rm --init "$image" python -m scripts.smoke_test "$@" ;;
    desktop)
        if desktop_exists; then
            if [ "$("$docker_cli" inspect --format '{{.State.Running}}' torcsrl-desktop)" = "true" ]; then
                echo "TORCS desktop is already running."
            else
                "$docker_cli" start torcsrl-desktop
            fi
            echo "Race viewer: http://127.0.0.1:8000/"
            echo "To replace it with a rebuilt image, run desktop-stop, then desktop."
            exit 0
        fi
        exec "$docker_cli" run -d --init --name torcsrl-desktop --shm-size=256m \
            -p 127.0.0.1:6080:6080 -p 127.0.0.1:8000:8000 \
            "$image" sh scripts/desktop.sh ;;
    desktop-stop)
        if desktop_exists; then
            exec "$docker_cli" rm -f torcsrl-desktop
        fi
        echo "TORCS desktop is already stopped." ;;
    desktop-logs) exec "$docker_cli" logs --tail 80 torcsrl-desktop ;;
    train)
        mkdir -p checkpoints
        exec "$docker_cli" run --rm --init \
            --mount "type=bind,source=$(pwd)/checkpoints,target=/workspace/checkpoints" \
            "$image" python -m scripts.train "$@" ;;
    *) echo "Usage: sh scripts/container.sh {build|smoke|train|desktop|desktop-stop|desktop-logs} [arguments...]" >&2; exit 2 ;;
esac
