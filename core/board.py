#imports
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, Optional, TypedDict, TypeAlias

if TYPE_CHECKING:
    from .piece import Piece

PieceOrNone: TypeAlias = Optional["Piece"]
PieceSnapshot: TypeAlias = tuple[type["Piece"], int, int, bool, bool, str, str]


# Defines the BoardSnapshot type.
class BoardSnapshot(TypedDict):
    grid: list[list[Optional[PieceSnapshot]]]
    side_to_move: bool
    castling_rights: int
    en_passant_target: Optional[tuple[int, int]]
    halfmove_clock: int
    fullmove_number: int
    position_counts: dict[str, int]
    move_notation_history: list[str]


# Defines the MoveHistoryRecord type.
class MoveHistoryRecord(TypedDict):
    snapshot: BoardSnapshot
    move: Move
    san: str


# Defines the TemporaryMoveUndo type.
class TemporaryMoveUndo(TypedDict):
    piece: "Piece"
    piece_from: tuple[int, int]
    piece_has_moved: bool
    captured_piece: PieceOrNone
    captured_coords: Optional[tuple[int, int]]
    rook: PieceOrNone
    rook_from: Optional[tuple[int, int]]
    rook_to: Optional[tuple[int, int]]
    rook_has_moved: Optional[bool]
    promotion_piece: PieceOrNone

# Defines the Move type.
@dataclass(frozen=True)
class Move:
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    promotion: Optional[str] = None
    is_castling: bool = False
    is_en_passant: bool = False


# Defines the Board type.
class Board:
    CASTLE_WHITE_KINGSIDE = 1 << 0
    CASTLE_WHITE_QUEENSIDE = 1 << 1
    CASTLE_BLACK_KINGSIDE = 1 << 2
    CASTLE_BLACK_QUEENSIDE = 1 << 3

    STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    # Handles __init__ operations.
    def __init__(self) -> None:
        self.grid: list[list[PieceOrNone]] = [[None for _ in range(8)] for _ in range(8)]
        self.side_to_move: bool = True
        self.castling_rights: int = 0
        self.en_passant_target: Optional[tuple[int, int]] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

        self.move_history: list[MoveHistoryRecord] = []
        self.move_notation_history: list[str] = []
        self.position_counts: dict[str, int] = {}

    # Handles reset operations.
    def reset(self) -> None:
        self.load_fen(self.STARTING_FEN)

    # Handles in_bounds operations.
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < 8 and 0 <= y < 8

    # Handles get_piece_class operations.
    def get_piece_class(self, char: str) -> type["Piece"]:
        from .bishop import Bishop
        from .king import King
        from .knight import Knight
        from .pawn import Pawn
        from .queen import Queen
        from .rook import Rook

        abbreviation_to_class: dict[str, type["Piece"]] = {
            "P": Pawn,
            "R": Rook,
            "N": Knight,
            "B": Bishop,
            "Q": Queen,
            "K": King,
            "p": Pawn,
            "r": Rook,
            "n": Knight,
            "b": Bishop,
            "q": Queen,
            "k": King,
        }
        return abbreviation_to_class[char]

    # Handles _castling_rights_to_fen operations.
    def _castling_rights_to_fen(self) -> str:
        bits_and_chars = [
            (Board.CASTLE_WHITE_KINGSIDE, "K"),
            (Board.CASTLE_WHITE_QUEENSIDE, "Q"),
            (Board.CASTLE_BLACK_KINGSIDE, "k"),
            (Board.CASTLE_BLACK_QUEENSIDE, "q"),
        ]
        fen_rights = ""
        for bit, char in bits_and_chars:
            if self.castling_rights & bit:
                fen_rights += char
        return fen_rights or "-"

    # Handles _fen_to_castling_rights operations.
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
            "q": Board.CASTLE_BLACK_QUEENSIDE,
        }
        for char in castling:
            rights |= char_to_bit[char]
        return rights

    # Handles _square_to_algebraic operations.
    def _square_to_algebraic(self, x: int, y: int) -> str:
        return f"{chr(ord('a') + y)}{8 - x}"

    # Handles _algebraic_to_square operations.
    def _algebraic_to_square(self, square: str) -> tuple[int, int]:
        if len(square) != 2 or not ("a" <= square[0] <= "h") or not ("1" <= square[1] <= "8"):
            raise ValueError(f"Invalid square: {square}")
        y = ord(square[0]) - ord("a")
        x = 8 - int(square[1])
        return x, y

    # Handles piece_at operations.
    def piece_at(self, x: int, y: int) -> PieceOrNone:
        if not self.in_bounds(x, y):
            return None
        return self.grid[x][y]

    # Handles to_fen operations.
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

    # Handles load_fen operations.
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
            raise ValueError("FEN must contain either 1 field or all 6 fields.")

        rows = piece_placement.split("/")
        if len(rows) != 8:
            raise ValueError("Piece placement field must contain 8 rows.")

        self.grid = [[None for _ in range(8)] for _ in range(8)]
        for x, row in enumerate(rows):
            y = 0
            for char in row:
                if char.isdigit():
                    y += int(char)
                    continue
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

        self.move_history = []
        self.move_notation_history = []
        self.position_counts = {}
        self._record_position()

    # Handles _position_key operations.
    def _position_key(self) -> str:
        fen_parts = self.to_fen().split()
        return " ".join(fen_parts[:4])

    # Handles _record_position operations.
    def _record_position(self) -> None:
        key = self._position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    # Handles _piece_snapshot operations.
    def _piece_snapshot(self, piece: PieceOrNone) -> Optional[PieceSnapshot]:
        if piece is None:
            return None
        return (
            piece.__class__,
            piece.x,
            piece.y,
            piece.color,
            piece.has_moved,
            piece.abbreviation,
            piece.name,
        )

    # Handles _snapshot operations.
    def _snapshot(self) -> BoardSnapshot:
        return {
            "grid": [[self._piece_snapshot(piece) for piece in row] for row in self.grid],
            "side_to_move": self.side_to_move,
            "castling_rights": self.castling_rights,
            "en_passant_target": self.en_passant_target,
            "halfmove_clock": self.halfmove_clock,
            "fullmove_number": self.fullmove_number,
            "position_counts": dict(self.position_counts),
            "move_notation_history": list(self.move_notation_history),
        }

    # Handles _restore operations.
    def _restore(self, snapshot: BoardSnapshot) -> None:
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        for x in range(8):
            for y in range(8):
                p = snapshot["grid"][x][y]
                if p is None:
                    continue
                cls, px, py, color, has_moved, abbreviation, name = p
                piece = cls(px, py, color, self)
                piece.has_moved = has_moved
                piece.abbreviation = abbreviation
                if name:
                    piece.name = name
                self.grid[x][y] = piece

        self.side_to_move = snapshot["side_to_move"]
        self.castling_rights = snapshot["castling_rights"]
        self.en_passant_target = snapshot["en_passant_target"]
        self.halfmove_clock = snapshot["halfmove_clock"]
        self.fullmove_number = snapshot["fullmove_number"]
        self.position_counts = dict(snapshot["position_counts"])
        self.move_notation_history = list(snapshot["move_notation_history"])

    # Handles iter_pieces operations.
    def iter_pieces(self, color: Optional[bool] = None) -> Iterator["Piece"]:
        for row in self.grid:
            for piece in row:
                if piece is None:
                    continue
                if color is None or piece.color == color:
                    yield piece

    # Handles find_king operations.
    def find_king(self, color: bool) -> tuple[int, int]:
        for piece in self.iter_pieces(color):
            if piece.abbreviation.lower() == "k":
                return piece.x, piece.y
        raise ValueError(f"King not found for color: {color}")

    # Handles _is_clear_line operations.
    def _is_clear_line(self, fx: int, fy: int, tx: int, ty: int) -> bool:
        dx = (tx - fx) and (1 if tx > fx else -1)
        dy = (ty - fy) and (1 if ty > fy else -1)
        x, y = fx + dx, fy + dy
        while (x, y) != (tx, ty):
            if self.grid[x][y] is not None:
                return False
            x += dx
            y += dy
        return True

    # Handles _piece_attacks_square operations.
    def _piece_attacks_square(self, piece: "Piece", x: int, y: int) -> bool:
        code = piece.abbreviation.lower()
        dx = x - piece.x
        dy = y - piece.y

        if code == "p":
            direction = -1 if piece.color else 1
            return dx == direction and abs(dy) == 1

        if code == "n":
            return (abs(dx), abs(dy)) in ((1, 2), (2, 1))

        if code == "k":
            return max(abs(dx), abs(dy)) == 1

        if code == "b":
            return abs(dx) == abs(dy) and self._is_clear_line(piece.x, piece.y, x, y)

        if code == "r":
            return (dx == 0 or dy == 0) and self._is_clear_line(piece.x, piece.y, x, y)

        if code == "q":
            straight = dx == 0 or dy == 0
            diagonal = abs(dx) == abs(dy)
            return (straight or diagonal) and self._is_clear_line(piece.x, piece.y, x, y)

        return False

    # Handles is_square_attacked operations.
    def is_square_attacked(self, x: int, y: int, by_color: bool) -> bool:
        for piece in self.iter_pieces(by_color):
            if self._piece_attacks_square(piece, x, y):
                return True
        return False

    # Handles in_check operations.
    def in_check(self, color: bool) -> bool:
        king_x, king_y = self.find_king(color)
        return self.is_square_attacked(king_x, king_y, not color)

    # Handles _pseudo_moves_for_piece operations.
    def _pseudo_moves_for_piece(self, piece: "Piece") -> list[Move]:
        moves: list[Move] = []
        code = piece.abbreviation.lower()

        if code == "p":
            direction = -1 if piece.color else 1
            start_row = 6 if piece.color else 1
            promote_row = 0 if piece.color else 7

            one_x = piece.x + direction
            if self.in_bounds(one_x, piece.y) and self.grid[one_x][piece.y] is None:
                if one_x == promote_row:
                    for p in "QRBN":
                        moves.append(Move(piece.x, piece.y, one_x, piece.y, promotion=p))
                else:
                    moves.append(Move(piece.x, piece.y, one_x, piece.y))

                two_x = piece.x + 2 * direction
                if piece.x == start_row and self.in_bounds(two_x, piece.y) and self.grid[two_x][piece.y] is None:
                    moves.append(Move(piece.x, piece.y, two_x, piece.y))

            for dy in (-1, 1):
                cx, cy = piece.x + direction, piece.y + dy
                if not self.in_bounds(cx, cy):
                    continue
                target = self.grid[cx][cy]
                if target is not None and target.color != piece.color:
                    if cx == promote_row:
                        for p in "QRBN":
                            moves.append(Move(piece.x, piece.y, cx, cy, promotion=p))
                    else:
                        moves.append(Move(piece.x, piece.y, cx, cy))

                if self.en_passant_target == (cx, cy):
                    side_piece = self.grid[piece.x][cy]
                    if side_piece is not None and side_piece.color != piece.color and side_piece.abbreviation.lower() == "p":
                        moves.append(Move(piece.x, piece.y, cx, cy, is_en_passant=True))

        elif code == "n":
            for dx, dy in ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)):
                nx, ny = piece.x + dx, piece.y + dy
                if not self.in_bounds(nx, ny):
                    continue
                target = self.grid[nx][ny]
                if target is None or target.color != piece.color:
                    moves.append(Move(piece.x, piece.y, nx, ny))

        elif code in ("b", "r", "q"):
            directions: list[tuple[int, int]] = []
            diagonal_directions: tuple[tuple[int, int], ...] = ((1, 1), (1, -1), (-1, 1), (-1, -1))
            orthogonal_directions: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))
            if code in ("b", "q"):
                for direction in diagonal_directions:
                    directions.append(direction)
            if code in ("r", "q"):
                for direction in orthogonal_directions:
                    directions.append(direction)

            for dx, dy in directions:
                for step in range(1, 8):
                    nx, ny = piece.x + step * dx, piece.y + step * dy
                    if not self.in_bounds(nx, ny):
                        break
                    target = self.grid[nx][ny]
                    if target is None:
                        moves.append(Move(piece.x, piece.y, nx, ny))
                        continue
                    if target.color != piece.color:
                        moves.append(Move(piece.x, piece.y, nx, ny))
                    break

        elif code == "k":
            for dx, dy in ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)):
                nx, ny = piece.x + dx, piece.y + dy
                if not self.in_bounds(nx, ny):
                    continue
                target = self.grid[nx][ny]
                if target is None or target.color != piece.color:
                    moves.append(Move(piece.x, piece.y, nx, ny))

            if piece.color:
                if self.castling_rights & self.CASTLE_WHITE_KINGSIDE:
                    if self._can_castle(True, kingside=True):
                        moves.append(Move(piece.x, piece.y, piece.x, piece.y + 2, is_castling=True))
                if self.castling_rights & self.CASTLE_WHITE_QUEENSIDE:
                    if self._can_castle(True, kingside=False):
                        moves.append(Move(piece.x, piece.y, piece.x, piece.y - 2, is_castling=True))
            else:
                if self.castling_rights & self.CASTLE_BLACK_KINGSIDE:
                    if self._can_castle(False, kingside=True):
                        moves.append(Move(piece.x, piece.y, piece.x, piece.y + 2, is_castling=True))
                if self.castling_rights & self.CASTLE_BLACK_QUEENSIDE:
                    if self._can_castle(False, kingside=False):
                        moves.append(Move(piece.x, piece.y, piece.x, piece.y - 2, is_castling=True))

        return moves

    # Handles _can_castle operations.
    def _can_castle(self, color: bool, kingside: bool) -> bool:
        king_row = 7 if color else 0
        king_col = 4
        rook_col = 7 if kingside else 0

        king = self.grid[king_row][king_col]
        rook = self.grid[king_row][rook_col]
        if king is None or rook is None:
            return False
        if king.abbreviation.lower() != "k" or rook.abbreviation.lower() != "r":
            return False
        if king.color != color or rook.color != color:
            return False

        if self.in_check(color):
            return False

        through_cols = [5, 6] if kingside else [3, 2]
        between_cols = [5, 6] if kingside else [1, 2, 3]

        for col in between_cols:
            if self.grid[king_row][col] is not None:
                return False

        for col in through_cols:
            if self.is_square_attacked(king_row, col, not color):
                return False

        return True

    # Handles _apply_move_no_record operations.
    def _apply_move_no_record(self, move: Move) -> tuple[PieceOrNone, tuple[int, int]]:
        piece = self.grid[move.from_x][move.from_y]
        if piece is None:
            raise ValueError("No piece on move start square.")

        captured_piece = None
        captured_coords = (move.to_x, move.to_y)

        if move.is_en_passant:
            capture_x = move.to_x + (1 if piece.color else -1)
            captured_piece = self.grid[capture_x][move.to_y]
            self.grid[capture_x][move.to_y] = None
            captured_coords = (capture_x, move.to_y)
        else:
            captured_piece = self.grid[move.to_x][move.to_y]

        self.grid[move.from_x][move.from_y] = None

        if move.is_castling:
            if move.to_y == 6:
                rook_from, rook_to = 7, 5
            else:
                rook_from, rook_to = 0, 3
            rook = self.grid[move.from_x][rook_from]
            if rook is None:
                raise ValueError("Castling rook is missing.")
            self.grid[move.from_x][rook_from] = None
            self.grid[move.from_x][rook_to] = rook
            rook.x, rook.y = move.from_x, rook_to
            rook.has_moved = True

        self.grid[move.to_x][move.to_y] = piece
        piece.x, piece.y = move.to_x, move.to_y
        piece.has_moved = True

        if move.promotion:
            promoted_class = self.get_piece_class(move.promotion if piece.color else move.promotion.lower())
            promoted_piece = promoted_class(move.to_x, move.to_y, piece.color, self)
            promoted_piece.has_moved = True
            self.grid[move.to_x][move.to_y] = promoted_piece

        return captured_piece, captured_coords

    # Handles _update_castling_rights_after_move operations.
    def _update_castling_rights_after_move(
        self, move: Move, moved_piece: "Piece", captured_piece: PieceOrNone, captured_coords: tuple[int, int]
    ) -> None:
        if moved_piece.abbreviation.lower() == "k":
            if moved_piece.color:
                self.castling_rights &= ~(self.CASTLE_WHITE_KINGSIDE | self.CASTLE_WHITE_QUEENSIDE)
            else:
                self.castling_rights &= ~(self.CASTLE_BLACK_KINGSIDE | self.CASTLE_BLACK_QUEENSIDE)

        if moved_piece.abbreviation.lower() == "r":
            if moved_piece.color and (move.from_x, move.from_y) == (7, 0):
                self.castling_rights &= ~self.CASTLE_WHITE_QUEENSIDE
            if moved_piece.color and (move.from_x, move.from_y) == (7, 7):
                self.castling_rights &= ~self.CASTLE_WHITE_KINGSIDE
            if (not moved_piece.color) and (move.from_x, move.from_y) == (0, 0):
                self.castling_rights &= ~self.CASTLE_BLACK_QUEENSIDE
            if (not moved_piece.color) and (move.from_x, move.from_y) == (0, 7):
                self.castling_rights &= ~self.CASTLE_BLACK_KINGSIDE

        if captured_piece is not None and captured_piece.abbreviation.lower() == "r":
            if captured_piece.color and captured_coords == (7, 0):
                self.castling_rights &= ~self.CASTLE_WHITE_QUEENSIDE
            if captured_piece.color and captured_coords == (7, 7):
                self.castling_rights &= ~self.CASTLE_WHITE_KINGSIDE
            if (not captured_piece.color) and captured_coords == (0, 0):
                self.castling_rights &= ~self.CASTLE_BLACK_QUEENSIDE
            if (not captured_piece.color) and captured_coords == (0, 7):
                self.castling_rights &= ~self.CASTLE_BLACK_KINGSIDE

    # Handles _move_leaves_king_in_check operations.
    def _move_leaves_king_in_check(self, move: Move, color: bool) -> bool:
        undo = self._apply_temporary_move(move)
        try:
            return self.in_check(color)
        finally:
            self._undo_temporary_move(undo)

    # Handles _apply_temporary_move operations.
    def _apply_temporary_move(self, move: Move) -> TemporaryMoveUndo:
        piece = self.grid[move.from_x][move.from_y]
        if piece is None:
            raise ValueError("No piece on move start square.")

        undo: TemporaryMoveUndo = {
            "piece": piece,
            "piece_from": (piece.x, piece.y),
            "piece_has_moved": piece.has_moved,
            "captured_piece": None,
            "captured_coords": None,
            "rook": None,
            "rook_from": None,
            "rook_to": None,
            "rook_has_moved": None,
            "promotion_piece": None,
        }

        if move.is_en_passant:
            capture_x = move.to_x + (1 if piece.color else -1)
            captured_piece = self.grid[capture_x][move.to_y]
            undo["captured_piece"] = captured_piece
            undo["captured_coords"] = (capture_x, move.to_y)
            self.grid[capture_x][move.to_y] = None
        else:
            captured_piece = self.grid[move.to_x][move.to_y]
            undo["captured_piece"] = captured_piece
            undo["captured_coords"] = (move.to_x, move.to_y)

        self.grid[move.from_x][move.from_y] = None

        if move.is_castling:
            if move.to_y == 6:
                rook_from, rook_to = 7, 5
            else:
                rook_from, rook_to = 0, 3
            rook = self.grid[move.from_x][rook_from]
            if rook is None:
                raise ValueError("Castling rook is missing.")
            undo["rook"] = rook
            undo["rook_from"] = (move.from_x, rook_from)
            undo["rook_to"] = (move.from_x, rook_to)
            undo["rook_has_moved"] = rook.has_moved
            self.grid[move.from_x][rook_from] = None
            self.grid[move.from_x][rook_to] = rook
            rook.x, rook.y = move.from_x, rook_to
            rook.has_moved = True

        self.grid[move.to_x][move.to_y] = piece
        piece.x, piece.y = move.to_x, move.to_y
        piece.has_moved = True

        if move.promotion:
            promoted_class = self.get_piece_class(move.promotion if piece.color else move.promotion.lower())
            promoted_piece = promoted_class(move.to_x, move.to_y, piece.color, self)
            promoted_piece.has_moved = True
            self.grid[move.to_x][move.to_y] = promoted_piece
            undo["promotion_piece"] = promoted_piece

        return undo

    # Handles _undo_temporary_move operations.
    def _undo_temporary_move(self, undo: TemporaryMoveUndo) -> None:
        piece = undo["piece"]
        from_x, from_y = undo["piece_from"]
        to_x, to_y = piece.x, piece.y

        self.grid[to_x][to_y] = None
        self.grid[from_x][from_y] = piece
        piece.x, piece.y = from_x, from_y
        piece.has_moved = undo["piece_has_moved"]

        captured_piece = undo["captured_piece"]
        captured_coords = undo["captured_coords"]
        if captured_piece is not None and captured_coords is not None:
            cx, cy = captured_coords
            self.grid[cx][cy] = captured_piece

        rook = undo["rook"]
        if rook is not None:
            rook_from = undo["rook_from"]
            rook_to = undo["rook_to"]
            rook_has_moved = undo["rook_has_moved"]
            if rook_from is None or rook_to is None or rook_has_moved is None:
                raise ValueError("Incomplete rook undo state for castling.")
            rook_from_x, rook_from_y = rook_from
            rook_to_x, rook_to_y = rook_to
            self.grid[rook_to_x][rook_to_y] = None
            self.grid[rook_from_x][rook_from_y] = rook
            rook.x, rook.y = rook_from_x, rook_from_y
            rook.has_moved = rook_has_moved

    # Handles get_legal_move_objects operations.
    def get_legal_move_objects(self, piece: PieceOrNone) -> list[Move]:
        if piece is None:
            return []
        moves: list[Move] = []
        for move in self._pseudo_moves_for_piece(piece):
            if not self._move_leaves_king_in_check(move, piece.color):
                moves.append(move)
        return moves

    # Handles get_legal_moves operations.
    def get_legal_moves(self, piece: PieceOrNone) -> list[tuple[int, int]]:
        return [(m.to_x, m.to_y) for m in self.get_legal_move_objects(piece)]

    # Handles get_all_legal_moves operations.
    def get_all_legal_moves(self, color: Optional[bool] = None) -> list[Move]:
        if color is None:
            color = self.side_to_move
        result: list[Move] = []
        for piece in self.iter_pieces(color):
            result.extend(self.get_legal_move_objects(piece))
        return result

    # Handles _matching_legal_move operations.
    def _matching_legal_move(self, from_x: int, from_y: int, to_x: int, to_y: int, promotion: Optional[str]) -> Optional[Move]:
        piece = self.grid[from_x][from_y]
        if piece is None or piece.color != self.side_to_move:
            return None
        for move in self.get_legal_move_objects(piece):
            if (move.to_x, move.to_y) != (to_x, to_y):
                continue
            if promotion and move.promotion and move.promotion.upper() == promotion.upper():
                return move
            if promotion is None:
                if move.promotion is None:
                    return move
                if move.promotion == "Q":
                    return move
        return None

    # Handles move_by_coords operations.
    def move_by_coords(self, from_x: int, from_y: int, to_x: int, to_y: int, promotion: Optional[str] = None) -> bool:
        if not (self.in_bounds(from_x, from_y) and self.in_bounds(to_x, to_y)):
            return False
        move = self._matching_legal_move(from_x, from_y, to_x, to_y, promotion)
        if move is None:
            return False
        self._execute_legal_move(move)
        return True

    # Handles move_by_uci operations.
    def move_by_uci(self, notation: str) -> bool:
        text = notation.strip()
        if len(text) not in (4, 5):
            return False
        try:
            from_x, from_y = self._algebraic_to_square(text[:2])
            to_x, to_y = self._algebraic_to_square(text[2:4])
        except ValueError:
            return False
        promotion = text[4].upper() if len(text) == 5 else None
        return self.move_by_coords(from_x, from_y, to_x, to_y, promotion)

    # Handles _move_is_capture operations.
    def _move_is_capture(self, move: Move) -> bool:
        if move.is_en_passant:
            return True
        return self.grid[move.to_x][move.to_y] is not None

    # Handles _move_to_san operations.
    def _move_to_san(self, move: Move) -> str:
        piece = self.grid[move.from_x][move.from_y]
        if piece is None:
            raise ValueError("Missing moving piece for SAN generation")

        if move.is_castling:
            san = "O-O" if move.to_y > move.from_y else "O-O-O"
        else:
            code = piece.abbreviation.upper() if piece.abbreviation.lower() != "p" else ""
            capture = self._move_is_capture(move)
            target_square = self._square_to_algebraic(move.to_x, move.to_y)

            disambiguation = ""
            if code:
                candidates: list["Piece"] = []
                for p in self.iter_pieces(piece.color):
                    if p is piece or p.abbreviation.upper() != piece.abbreviation.upper():
                        continue
                    for alt in self.get_legal_move_objects(p):
                        if (alt.to_x, alt.to_y) == (move.to_x, move.to_y):
                            candidates.append(p)
                            break

                if candidates:
                    same_file = False
                    same_rank = False
                    for candidate in candidates:
                        if candidate.y == piece.y:
                            same_file = True
                        if candidate.x == piece.x:
                            same_rank = True
                    if not same_file:
                        disambiguation = chr(ord("a") + piece.y)
                    elif not same_rank:
                        disambiguation = str(8 - piece.x)
                    else:
                        disambiguation = f"{chr(ord('a') + piece.y)}{8 - piece.x}"

            if not code and capture:
                disambiguation = chr(ord("a") + piece.y)

            san = f"{code}{disambiguation}{'x' if capture else ''}{target_square}"
            if move.promotion:
                san += f"={move.promotion.upper()}"

        undo = self._apply_temporary_move(move)
        self.side_to_move = not self.side_to_move
        in_check = self.in_check(self.side_to_move)
        is_mate = in_check and not self.get_all_legal_moves(self.side_to_move)
        self.side_to_move = not self.side_to_move
        self._undo_temporary_move(undo)

        if is_mate:
            san += "#"
        elif in_check:
            san += "+"
        return san

    # Handles _execute_legal_move operations.
    def _execute_legal_move(self, move: Move) -> None:
        snapshot = self._snapshot()
        moved_piece = self.grid[move.from_x][move.from_y]
        if moved_piece is None:
            raise ValueError("No piece found on legal move source square.")
        san = self._move_to_san(move)

        captured_piece, captured_coords = self._apply_move_no_record(move)

        self._update_castling_rights_after_move(move, moved_piece, captured_piece, captured_coords)

        if moved_piece.abbreviation.lower() == "p" and abs(move.to_x - move.from_x) == 2:
            self.en_passant_target = ((move.from_x + move.to_x) // 2, move.from_y)
        else:
            self.en_passant_target = None

        if moved_piece.abbreviation.lower() == "p" or captured_piece is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        self.side_to_move = not self.side_to_move
        if self.side_to_move:
            self.fullmove_number += 1

        self.move_history.append({"snapshot": snapshot, "move": move, "san": san})
        self.move_notation_history.append(san)
        self._record_position()

    # Handles undo_move operations.
    def undo_move(self) -> bool:
        if not self.move_history:
            return False
        record = self.move_history.pop()
        self._restore(record["snapshot"])
        return True

    # Handles parse_san operations.
    def parse_san(self, notation: str) -> Optional[Move]:
        text = notation.strip()
        if not text:
            return None

        normalized = text.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
        if normalized in ("O-O", "O-O+", "O-O#"):
            for move in self.get_all_legal_moves(self.side_to_move):
                if move.is_castling and move.to_y > move.from_y:
                    return move
            return None
        if normalized in ("O-O-O", "O-O-O+", "O-O-O#"):
            for move in self.get_all_legal_moves(self.side_to_move):
                if move.is_castling and move.to_y < move.from_y:
                    return move
            return None

        while normalized and normalized[-1] in "+#?!":
            normalized = normalized[:-1]

        promotion = None
        if "=" in normalized:
            normalized, promo = normalized.split("=", 1)
            if not promo:
                return None
            promotion = promo[0].upper()

        piece_letter = "P"
        idx = 0
        if normalized and normalized[0] in "KQRBN":
            piece_letter = normalized[0]
            idx = 1

        if len(normalized[idx:]) < 2:
            return None

        target_text = normalized[-2:]
        try:
            to_x, to_y = self._algebraic_to_square(target_text)
        except ValueError:
            return None

        body = normalized[idx:-2]
        is_capture = "x" in body
        body = body.replace("x", "")

        from_file = None
        from_rank = None
        for ch in body:
            if "a" <= ch <= "h":
                from_file = ord(ch) - ord("a")
            elif "1" <= ch <= "8":
                from_rank = 8 - int(ch)

        legal = self.get_all_legal_moves(self.side_to_move)
        candidates: list[Move] = []
        for move in legal:
            piece = self.grid[move.from_x][move.from_y]
            if piece is None:
                continue
            if piece.abbreviation.upper() != piece_letter:
                continue
            if (move.to_x, move.to_y) != (to_x, to_y):
                continue
            if promotion and move.promotion != promotion:
                continue
            if is_capture and not self._move_is_capture(move):
                continue
            if from_file is not None and move.from_y != from_file:
                continue
            if from_rank is not None and move.from_x != from_rank:
                continue
            candidates.append(move)

        if len(candidates) == 1:
            return candidates[0]
        return None

    # Handles play_notation operations.
    def play_notation(self, notation: str) -> bool:
        text = notation.strip()
        if not text:
            return False

        if self.move_by_uci(text):
            return True

        move = self.parse_san(text)
        if move is None:
            return False
        self._execute_legal_move(move)
        return True

    # Handles is_checkmate operations.
    def is_checkmate(self, color: Optional[bool] = None) -> bool:
        if color is None:
            color = self.side_to_move
        return self.in_check(color) and not self.get_all_legal_moves(color)

    # Handles is_stalemate operations.
    def is_stalemate(self, color: Optional[bool] = None) -> bool:
        if color is None:
            color = self.side_to_move
        return (not self.in_check(color)) and not self.get_all_legal_moves(color)

    # Handles is_draw_by_fifty_move_rule operations.
    def is_draw_by_fifty_move_rule(self) -> bool:
        return self.halfmove_clock >= 100

    # Handles is_draw_by_threefold_repetition operations.
    def is_draw_by_threefold_repetition(self) -> bool:
        return any(count >= 3 for count in self.position_counts.values())

    # Handles is_draw_by_insufficient_material operations.
    def is_draw_by_insufficient_material(self) -> bool:
        pieces = list(self.iter_pieces())
        non_kings = [p for p in pieces if p.abbreviation.lower() != "k"]
        if not non_kings:
            return True

        if len(non_kings) == 1:
            return non_kings[0].abbreviation.lower() in ("b", "n")

        if len(non_kings) == 2:
            a, b = non_kings
            a_code, b_code = a.abbreviation.lower(), b.abbreviation.lower()
            if a_code == "n" and b_code == "n":
                return True
            if a_code == "b" and b_code == "b":
                a_dark = (a.x + a.y) % 2
                b_dark = (b.x + b.y) % 2
                return a_dark == b_dark

        return False

    # Handles is_draw operations.
    def is_draw(self) -> bool:
        return (
            self.is_stalemate()
            or self.is_draw_by_fifty_move_rule()
            or self.is_draw_by_threefold_repetition()
            or self.is_draw_by_insufficient_material()
        )
