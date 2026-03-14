# Chess GUI and Engine

Tkinter-based chess board with a move timeline, notation tracking, replay controls, and supporting board logic/tests.

## Highlights
- `main.py` launches `gui.app.ChessGUI`, which wires together the canvas, animation options, notation panel, and save/load controls.
- `gui` handles the visual state (drag/drop, move highlighting, flip board, undo/redo, live notation list) while `game.ChessGame` maintains the board history, timeline navigation, and JSON save/load helpers.
- `core` defines every piece type, the board representation, and move generation.
- `tests/` cover move legality, special moves, FEN serialization, game saving/loading, and end-state detection.

## Running
Install the default Python tooling and ensure `tkinter` is available, then from the repo root execute:

```bash
python -m chess.main
```

The GUI opens by default; use the buttons to train, undo, load/save timelines, or flip the board. You can rerun moves through the timeline or load saved JSON files from `saves/`.

Run the unit tests with:

```bash
python -m pytest tests
```

## Structure
- `core/`: piece definitions plus the board implementation and move-check helpers.
- `game/`: `ChessGame` (timeline, play/save/load, history stitching) and related DTOs.
- `gui/`: Tkinter application and drag/animation input handling.
- `saves/`: pre-built replay files for manual playback and sharing.
