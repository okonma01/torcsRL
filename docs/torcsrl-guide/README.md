# torcsRL introduction

Open `dist/index.html` in a browser, or serve it from the repository root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs/torcsrl-guide/dist
```

Then visit <http://127.0.0.1:8765/>. Stop the server with Ctrl+C.

This is a local, buildless guide. `dist/` contains HTML, CSS, and JavaScript.
The existing simulator screenshot remains in `dist/assets/`. No training starts
from this page.

The guide introduces this modified workspace through observations, actions, and
three complete Python examples, then briefly explains the Linux simulator on a
Mac and the limits of reproducing results. It contains no research plan.

The examples require the local simulator gateway and native Python dependencies.
Keep the guide in sync with `gym_torcs/env.py`, `constants.py`, `remote.py`, and
the launchers when changing observations, rewards, resets, or simulator support.

A private Sites project was registered, but source preparation/publication was
blocked by automatic approval review. Nothing was published. Its identity is
retained in `.openai/hosting.json` so any approved future publication can reuse
that project rather than creating a duplicate.
