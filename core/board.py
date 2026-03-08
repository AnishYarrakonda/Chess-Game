# imports
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .piece import Piece

class Board:

    def __init__(self) -> None:
        self.grid: list[list[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.history: list[list[list[Optional[Piece]]]] = []
        self.side_to_move: bool = True
        self.castling_rights: str = "-"
        self.en_passant_target: Optional[tuple[int, int]] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < 8 and 0 <= y < 8
    
    def get_piece_class(self, char: str):
        from .pawn import Pawn
        from .rook import Rook
        from .knight import Knight
        from .bishop import Bishop
        from .queen import Queen
        from .king import King

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
        return abbreviation_to_class[char]

    def _normalize_castling_rights(self, rights: str) -> str:
        if rights == "-":
            return rights
        ordered = "".join(ch for ch in "KQkq" if ch in rights)
        return ordered if ordered else "-"

    def _square_to_algebraic(self, x: int, y: int) -> str:
        return f"{chr(ord('a') + y)}{8 - x}"
    
    def _algebraic_to_square(self, square: str) -> tuple[int, int]:
        if len(square) != 2 or square[0] < "a" or square[0] > "h" or square[1] < "1" or square[1] > "8":
            raise ValueError(f"Invalid en passant target square: {square}")
        y = ord(square[0]) - ord("a")
        x = 8 - int(square[1])
        return x, y

    def to_fen(self) -> str:
        fen_rows: list[str] = []
        for row in self.grid:
            empty_count = 0
            row_fen = ""
            for piece in row:
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_fen += str(empty_count)
                        empty_count = 0
                    row_fen += piece.abbreviation
            if empty_count > 0:
                row_fen += str(empty_count)
            fen_rows.append(row_fen)

        piece_placement = "/".join(fen_rows)
        side = "w" if self.side_to_move else "b"
        castling = self._normalize_castling_rights(self.castling_rights)
        en_passant = "-" if self.en_passant_target is None else self._square_to_algebraic(*self.en_passant_target)
        return f"{piece_placement} {side} {castling} {en_passant} {self.halfmove_clock} {self.fullmove_number}"
    
    def load_fen(self, fen: str) -> None:
        parts = fen.strip().split()
        if len(parts) == 1:
            piece_placement = parts[0]
            side = "w"
            castling = "-"
            en_passant = "-"
            halfmove = "0"
            fullmove = "1"
        elif len(parts) == 6:
            piece_placement, side, castling, en_passant, halfmove, fullmove = parts
        else:
            raise ValueError("FEN must contain either 1 field (piece placement only) or all 6 fields.")

        rows = piece_placement.split('/')
        if len(rows) != 8:
            raise ValueError("Piece placement field must contain 8 rows.")

        self.grid = [[None for _ in range(8)] for _ in range(8)]
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
            if y != 8:
                raise ValueError(f"Invalid row in piece placement field: {row}")

        if side not in ("w", "b"):
            raise ValueError("Side to move field must be 'w' or 'b'.")
        self.side_to_move = side == "w"

        if castling != "-" and any(ch not in "KQkq" for ch in castling):
            raise ValueError("Castling rights field must contain only KQkq or '-'.")
        self.castling_rights = self._normalize_castling_rights(castling)

        self.en_passant_target = None if en_passant == "-" else self._algebraic_to_square(en_passant)
        self.halfmove_clock = int(halfmove)
        self.fullmove_number = int(fullmove)
