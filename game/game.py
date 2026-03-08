#imports
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, TypedDict, cast

try:
    from core.board import Board
except ModuleNotFoundError:
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.board import Board


# Defines the SavedGame type.
class SavedGame(TypedDict):
    timeline: list[str]
    timeline_index: int
    current_fen: str
    move_notation_history: list[str]
    timeline_notations: list[str]
    timeline_moves: list[list[int]]


# Defines the TimelineMove type.
class TimelineMove(TypedDict):
    from_x: int
    from_y: int
    to_x: int
    to_y: int


# Defines the ChessGame type.
class ChessGame:
    # Handles __init__ operations.
    def __init__(self, fen: str = Board.STARTING_FEN) -> None:
        self.board: Board = Board()
        self.board.load_fen(fen)
        self.timeline: list[str] = [self.board.to_fen()]
        self.timeline_index: int = 0
        self.timeline_notations: list[str] = []
        self.timeline_moves: list[TimelineMove] = []

    # Handles current_fen operations.
    def current_fen(self) -> str:
        return self.timeline[self.timeline_index]

    # Handles _truncate_future_if_needed operations.
    def _truncate_future_if_needed(self) -> None:
        if self.timeline_index < len(self.timeline) - 1:
            self.timeline = self.timeline[: self.timeline_index + 1]
            self.timeline_notations = self.timeline_notations[: self.timeline_index]
            self.timeline_moves = self.timeline_moves[: self.timeline_index]

    # Handles _sync_board_history_for_index operations.
    def _sync_board_history_for_index(self) -> None:
        self.board.move_notation_history = list(self.timeline_notations[: self.timeline_index])

    # Handles play operations.
    def play(self, notation: str) -> bool:
        self._truncate_future_if_needed()
        if not self.board.play_notation(notation):
            return False
        self.timeline.append(self.board.to_fen())
        last_san = self.board.move_notation_history[-1] if self.board.move_notation_history else notation
        self.timeline_notations.append(last_san)
        if self.board.move_history:
            move_obj = self.board.move_history[-1]["move"]
            self.timeline_moves.append(
                {
                    "from_x": move_obj.from_x,
                    "from_y": move_obj.from_y,
                    "to_x": move_obj.to_x,
                    "to_y": move_obj.to_y,
                }
            )
        self.timeline_index += 1
        return True

    # Handles play_coords operations.
    def play_coords(
        self,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        promotion: Optional[str] = None,
    ) -> bool:
        self._truncate_future_if_needed()
        if not self.board.move_by_coords(from_x, from_y, to_x, to_y, promotion):
            return False
        self.timeline.append(self.board.to_fen())
        last_san = self.board.move_notation_history[-1] if self.board.move_notation_history else ""
        self.timeline_notations.append(last_san)
        if self.board.move_history:
            move_obj = self.board.move_history[-1]["move"]
            self.timeline_moves.append(
                {
                    "from_x": move_obj.from_x,
                    "from_y": move_obj.from_y,
                    "to_x": move_obj.to_x,
                    "to_y": move_obj.to_y,
                }
            )
        self.timeline_index += 1
        return True

    # Handles step_backward operations.
    def step_backward(self) -> bool:
        if self.timeline_index == 0:
            return False
        self.timeline_index -= 1
        self.board.load_fen(self.timeline[self.timeline_index])
        self._sync_board_history_for_index()
        return True

    # Handles step_forward operations.
    def step_forward(self) -> bool:
        if self.timeline_index >= len(self.timeline) - 1:
            return False
        self.timeline_index += 1
        self.board.load_fen(self.timeline[self.timeline_index])
        self._sync_board_history_for_index()
        return True

    # Handles go_to operations.
    def go_to(self, index: int) -> bool:
        if index < 0 or index >= len(self.timeline):
            return False
        self.timeline_index = index
        self.board.load_fen(self.timeline[self.timeline_index])
        self._sync_board_history_for_index()
        return True

    # Handles last_move_for_index operations.
    def last_move_for_index(self, index: Optional[int] = None) -> Optional[TimelineMove]:
        idx = self.timeline_index if index is None else index
        if idx <= 0 or idx > len(self.timeline_moves):
            return None
        return self.timeline_moves[idx - 1]

    # Handles save operations.
    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        data: SavedGame = {
            "timeline": self.timeline,
            "timeline_index": self.timeline_index,
            "current_fen": self.board.to_fen(),
            "move_notation_history": list(self.board.move_notation_history),
            "timeline_notations": list(self.timeline_notations),
            "timeline_moves": [
                [move["from_x"], move["from_y"], move["to_x"], move["to_y"]]
                for move in self.timeline_moves
            ],
        }
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Handles load operations.
    @classmethod
    def load(cls, path: str | Path) -> ChessGame:
        source = Path(path)
        raw_obj: object = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(raw_obj, dict):
            raise ValueError("Saved game file must contain a JSON object.")
        raw: dict[str, object] = cast(dict[str, object], raw_obj)

        timeline_obj: object = raw.get("timeline")
        if not isinstance(timeline_obj, list) or not timeline_obj:
            raise ValueError("Saved game is missing a valid timeline.")
        timeline = [str(item) for item in cast(list[object], timeline_obj)]

        index_obj: object = raw.get("timeline_index", 0)
        if not isinstance(index_obj, int) or index_obj < 0 or index_obj >= len(timeline):
            raise ValueError("Saved game has an invalid timeline index.")
        index: int = index_obj

        game = cls(timeline[0])
        game.timeline = timeline
        game.timeline_index = index
        game.board.load_fen(game.timeline[index])

        notations: object = raw.get("move_notation_history", [])
        if isinstance(notations, list):
            game.board.move_notation_history = [str(x) for x in cast(list[object], notations)]

        timeline_notations_obj: object = raw.get("timeline_notations", game.board.move_notation_history)
        if isinstance(timeline_notations_obj, list):
            game.timeline_notations = [str(item) for item in cast(list[object], timeline_notations_obj)]
        else:
            game.timeline_notations = list(game.board.move_notation_history)

        timeline_moves_obj: object = raw.get("timeline_moves", [])
        parsed_moves: list[TimelineMove] = []
        if isinstance(timeline_moves_obj, list):
            for row in cast(list[object], timeline_moves_obj):
                if isinstance(row, list):
                    row = cast(list[object], row)
                    if (
                        len(row) == 4
                        and all(isinstance(v, int) for v in row)
                    ):
                        from_x, from_y, to_x, to_y = row
                        parsed_moves.append(
                            {
                                "from_x": cast(int, from_x),
                                "from_y": cast(int, from_y),
                                "to_x": cast(int, to_x),
                                "to_y": cast(int, to_y),
                            }
                        )
        game.timeline_moves = parsed_moves
        game._sync_board_history_for_index()
        return game
