# Digicoach

A small bodyweight-training web app. The user answers a short form (email, age, sex, height, weight and goal), gets their BMI and basal metabolic rate, and receives a session of 3–5 exercises suggested by Claude. Each exercise shows an animated figure (start and end of the movement, alternating), the number of reps and a countdown timer.

The app is available in English (default) and Spanish, with a light and a dark theme.

## Project structure

| Path | Contents |
| --- | --- |
| `app/index.html` | The main app: form, results, Claude-suggested routine and session player. |
| `app/exercise-manager.html` | The earlier page for adding, editing and deleting exercises with an image. |
| `data/exercises.json` | The 15 exercises in the catalog (Spanish and English names and descriptions, muscle group and image references). |
| `assets/exercises/` | Start and end illustrations for each exercise (SVG, 400×300). |
| `tools/` | Python scripts that draw the stick-figure illustrations (need `cairosvg` and `pillow`). |

## How it runs

The app is published as a Claude artifact and relies on runtime capabilities that the Claude viewer provides through `window.claude.use(...)`:

- `db` stores the exercise catalog (`ejercicios` collection) and one record per person (`personas/<user id>`). Each person can only read and write their own record; only editors can read everyone's.
- `assets` serves the exercise images at `/_blob/<id>`. The ids in `data/exercises.json` (`imagenInicio`, `imagenFin`) point to the copies stored in the artifact.
- `sample` asks Claude for the exercise suggestions on the viewer's own Claude account, so no API key is stored in the page.
- `user` identifies the viewer so their record can be kept private.

Opened directly from GitHub or a static host, the page loads but can't save data or suggest exercises, because those capabilities aren't available outside Claude.

## Running it outside Claude

`server/` is a small Node server (Node 20.12 or later) that stands in for the Claude runtime:

```bash
cd server
npm install
cp .env.example .env   # then put your key in ANTHROPIC_API_KEY
npm start              # open http://localhost:8080/
```

- `app/claude-shim.js` defines `window.claude` only when the page isn't running inside Claude, so the same `index.html` works in both places.
- Exercise suggestions go to `POST /api/suggest`; the server calls the Claude API with the key from `server/.env`, which never reaches the browser. The model defaults to `claude-opus-5` and can be changed with `ANTHROPIC_MODEL`.
- The catalog is read from `data/exercises.json`, and `/_blob/<id>` is served from `assets/exercises/`.
- Each person's answers are kept in the browser's `localStorage`, so they stay on that device only.
- `exercise-manager.html` still needs Claude, because it uploads images to the artifact.

## Regenerating the illustrations

```bash
pip install cairosvg pillow
cd tools
python generate_figures.py        # the first 10 exercises
python generate_figures_extra.py  # the 5 added later
```

The figures are written to `tools/svg/`.
