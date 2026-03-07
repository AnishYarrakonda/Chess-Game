# imports
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .piece import Piece
    from .pawn import Pawn
    from .rook import Rook
    from .knight import Knight
    from .bishop import Bishop
    from .queen import Queen
    from .king import King

class Board:

    abbreviation_to_class: dict[str, type[Piece]] = {
            'P': Pawn,
            'R': Rook,
            'N': Knight,
            'B': Bishop,
            'Q': Queen,
            'K': King,
            'p': Pawn,
            'r': Rook,
            'n': Knight,
            'b': Bishop,
            'q': Queen,
            'k': King
        }

    def __init__(self) -> None:
        self.grid: list[list[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.history: list[list[list[Optional[Piece]]]] = []

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < 8 and 0 <= y < 8
    
    def get_piece_class(self, char: str):
        return Board.abbreviation_to_class[char]

    def to_fen(self) -> str:
        fen: str = ""
        for row in self.grid:
            empty_count = 0
            for piece in row:
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    fen += piece.abbreviation
            if empty_count > 0:
                fen += str(empty_count)
            fen += '/'
        return fen[:-1]
    
    def load_fen(self, fen: str) -> None:
        rows = fen.split('/')
        for x, row in enumerate(rows):
            y = 0
            for char in row:
                if char.isdigit():
                    y += int(char)
                else:
                    color = char.isupper()
                    piece_class = self.get_piece_class(char)
                    piece = piece_class(x, y, color, self)
                    self.grid[x][y] = piece
                    y += 1