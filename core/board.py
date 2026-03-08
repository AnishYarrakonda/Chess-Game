# imports
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .piece import Piece

# stores the board for the game
class Board:
    CASTLE_WHITE_KINGSIDE = 1 << 0
    CASTLE_WHITE_QUEENSIDE = 1 << 1
    CASTLE_BLACK_KINGSIDE = 1 << 2
    CASTLE_BLACK_QUEENSIDE = 1 << 3

    # creates a new board
    def __init__(self) -> None:
        self.grid: list[list[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.history: list[list[list[Optional[Piece]]]] = []
        self.side_to_move: bool = True
        self.castling_rights: int = 0
        self.en_passant_target: Optional[tuple[int, int]] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

    # checks if a square is in the bounds of the board
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < 8 and 0 <= y < 8
    
    # gets the class of a piece based on its abbreviation
    def get_piece_class(self, char: str):
        from .pawn import Pawn
        from .rook import Rook
        from .knight import Knight
        from .bishop import Bishop
        from .queen import Queen
        from .king import King

        # dictionary mapping piece abbreviations to their classes
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

    # turns a castling-rights bitmask into fen text
    def _castling_rights_to_fen(self) -> str:
        bits_and_chars = [
            (Board.CASTLE_WHITE_KINGSIDE, "K"),
            (Board.CASTLE_WHITE_QUEENSIDE, "Q"),
            (Board.CASTLE_BLACK_KINGSIDE, "k"),
            (Board.CASTLE_BLACK_QUEENSIDE, "q")
        ]
        rights = [bool(self.castling_rights & bit) for bit, _ in bits_and_chars]
        if all(not right for right in rights):
            return "-"

        fen_rights = ""
        for bit, char in bits_and_chars:
            if self.castling_rights & bit:
                fen_rights += char
        return fen_rights

    # parses fen castling text into a bitmask
    def _fen_to_castling_rights(self, castling: str) -> int:
        if castling == "-":
            return 0
        if any(ch not in "KQkq" for ch in castling):
            raise ValueError("Castling rights field must contain only KQkq or '-'.")

        rights = 0
        char_to_bit = {
            "K": Board.CASTLE_WHITE_KINGSIDE,
            "Q": Board.CASTLE_WHITE_QUEENSIDE,
            "k": Board.CASTLE_BLACK_KINGSIDE,
            "q": Board.CASTLE_BLACK_QUEENSIDE
        }
        for char in castling:
            rights |= char_to_bit[char]
        return rights

    # converts a square coordinate to algebraic notation
    def _square_to_algebraic(self, x: int, y: int) -> str:
        return f"{chr(ord('a') + y)}{8 - x}"
    
    # converts algebraic notation to square coordinates
    def _algebraic_to_square(self, square: str) -> tuple[int, int]:
        if len(square) != 2 or square[0] < "a" or square[0] > "h" or square[1] < "1" or square[1] > "8":
            raise ValueError(f"Invalid en passant target square: {square}")
        y = ord(square[0]) - ord("a")
        x = 8 - int(square[1])
        return x, y

    # takes the current board state and turns it into an FEN string
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
        castling = self._castling_rights_to_fen()
        en_passant = "-" if self.en_passant_target is None else self._square_to_algebraic(*self.en_passant_target)
        return f"{piece_placement} {side} {castling} {en_passant} {self.halfmove_clock} {self.fullmove_number}"
    
    # loads the given position based on the FEN string
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

        self.castling_rights = self._fen_to_castling_rights(castling)

        self.en_passant_target = None if en_passant == "-" else self._algebraic_to_square(en_passant)
        self.halfmove_clock = int(halfmove)
        self.fullmove_number = int(fullmove)

    # find the white/black king's location
    def find_king(self, color: bool) -> tuple[int, int]:
        for x in range(8):
            for y in range(8):
                piece = self.grid[x][y]
                if piece is not None and piece.abbreviation.lower() == "k" and piece.color == color:
                    return x, y
        raise ValueError(f"King not found for color: {color}")

    # returns if a square is attacked by a given color
    def is_square_attacked(self, x: int, y: int, by_color: bool) -> bool:
        for row in self.grid:
            for piece in row:
                if piece is None or piece.color != by_color:
                    continue

                piece_code = piece.abbreviation.lower()

                if piece_code == "p":
                    direction = 1 if piece.color else -1
                    attack_row = piece.x + direction
                    if (attack_row, piece.y - 1) == (x, y) or (attack_row, piece.y + 1) == (x, y):
                        return True
                    continue

                if piece_code == "k":
                    if max(abs(piece.x - x), abs(piece.y - y)) == 1:
                        return True
                    continue

                if (x, y) in piece.get_valid_moves():
                    return True
        return False

    # returns if the white/black king is in check
    def in_check(self, color: bool) -> bool:
        king_x, king_y = self.find_king(color)
        return self.is_square_attacked(king_x, king_y, not color)

    # simulates a move and returns True if own king is left in check
    def _move_leaves_king_in_check(self, piece: Piece, x: int, y: int) -> bool:
        from_x, from_y = piece.x, piece.y
        captured_piece = self.grid[x][y]
        previous_has_moved = piece.has_moved

        self.grid[from_x][from_y] = None
        self.grid[x][y] = piece
        piece.x = x
        piece.y = y
        piece.has_moved = True

        in_check = self.in_check(piece.color)

        piece.x = from_x
        piece.y = from_y
        piece.has_moved = previous_has_moved
        self.grid[from_x][from_y] = piece
        self.grid[x][y] = captured_piece

        return in_check

    # returns legal moves for a piece (pseudo-legal filtered by king safety)
    def get_legal_moves(self, piece: Piece) -> list[tuple[int, int]]:
        legal_moves: list[tuple[int, int]] = []
        for x, y in piece.get_valid_moves():
            if not self._move_leaves_king_in_check(piece, x, y):
                legal_moves.append((x, y))
        return legal_moves
