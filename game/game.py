from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from core.board import Board


class SavedGame(TypedDict):
    timeline: list[str]
    timeline_index: int
    current_fen: str
    move_notation_history: list[str]


class ChessGame:
    def __init__(self, fen: str = Board.STARTING_FEN) -> None:
        self.board: Board = Board()
        self.board.load_fen(fen)
        self.timeline: list[str] = [self.board.to_fen()]
        self.timeline_index: int = 0

    def current_fen(self) -> str:
        return self.timeline[self.timeline_index]

    def _truncate_future_if_needed(self) -> None:
        if self.timeline_index < len(self.timeline) - 1:
            self.timeline = self.timeline[: self.timeline_index + 1]

    def play(self, notation: str) -> bool:
        self._truncate_future_if_needed()
        if not self.board.play_notation(notation):
            return False
        self.timeline.append(self.board.to_fen())
        self.timeline_index += 1
        return True

    def step_backward(self) -> bool:
        if self.timeline_index == 0:
            return False
        self.timeline_index -= 1
        self.board.load_fen(self.timeline[self.timeline_index])
        return True

    def step_forward(self) -> bool:
        if self.timeline_index >= len(self.timeline) - 1:
            return False
        self.timeline_index += 1
        self.board.load_fen(self.timeline[self.timeline_index])
        return True

    def go_to(self, index: int) -> bool:
        if index < 0 or index >= len(self.timeline):
            return False
        self.timeline_index = index
        self.board.load_fen(self.timeline[self.timeline_index])
        return True

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        data: SavedGame = {
            "timeline": self.timeline,
            "timeline_index": self.timeline_index,
            "current_fen": self.board.to_fen(),
            "move_notation_history": list(self.board.move_notation_history),
        }
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> ChessGame:
        source = Path(path)
        raw = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Saved game file must contain a JSON object.")

        timeline_obj = raw.get("timeline")
        if not isinstance(timeline_obj, list) or not timeline_obj:
            raise ValueError("Saved game is missing a valid timeline.")
        timeline = [str(item) for item in timeline_obj]

        index_obj = raw.get("timeline_index", 0)
        if not isinstance(index_obj, int) or index_obj < 0 or index_obj >= len(timeline):
            raise ValueError("Saved game has an invalid timeline index.")
        index = cast(int, index_obj)

        game = cls(timeline[0])
        game.timeline = timeline
        game.timeline_index = index
        game.board.load_fen(game.timeline[index])

        notations = raw.get("move_notation_history", [])
        if isinstance(notations, list):
            game.board.move_notation_history = [str(x) for x in notations]
        return game
