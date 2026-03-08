#imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from .board import Board

# piece superclass
class Piece(ABC):

    # constructor - use (x, y, color, board) to match subclasses
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        self.color: bool = color
        self.x: int = x
        self.y: int = y
        self.board: Board = board
        self.has_moved: bool = False
        self.name: str = self.__class__.__name__
        self.abbreviation: str = ""

    # moves the piece to a new position and updates the board state
    def move(self, x: int, y: int) -> None:
        self.board.grid[self.x][self.y] = None

        self.x: int = x
        self.y: int = y

        self.board.grid[self.x][self.y] = self

        self.has_moved = True

    # creates a generator that yields valid moves in a given direction 
    # until it hits the edge of the board or another piece
    def slide(self, dx: int, dy: int) -> Generator[tuple[int, int], None, None]:
        for step in range(1, 8):
            new_x = self.x + dx * step
            new_y = self.y + dy * step
            if not self.board.in_bounds(new_x, new_y):
                break
            piece = self.board.grid[new_x][new_y]
            if piece is not None:
                if piece.color != self.color:
                    yield (new_x, new_y)
                break
            yield (new_x, new_y)

    # slides in all given directions and yields valid moves
    def slide_all(self, directions: list[tuple[int, int]]) -> Generator[tuple[int, int], None, None]:
        for dx, dy in directions:
            yield from self.slide(dx, dy)

    # gets valid moves for the piece (to be implemented by subclasses)
    @abstractmethod
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        raise NotImplementedError

    # checks if a given position is occupied by an opponent's piece
    def is_opponent_piece(self, x: int, y: int) -> bool:
        if not self.board.in_bounds(x, y):
            return False
        piece = self.board.grid[x][y]
        return piece is not None and piece.color != self.color
    
    # checks if a given position is occupied by a friendly piece
    def is_friendly_piece(self, x: int, y: int) -> bool:
        if not self.board.in_bounds(x, y):
            return False
        piece = self.board.grid[x][y]
        return piece is not None and piece.color == self.color

    # makes a copy of the piece for use in move generation and board state simulation
    def copy(self, board: Board) -> Piece:
        return self.__class__(self.x, self.y, self.color, board)

    # string representation of the piece for debugging
    def __str__(self) -> str:
        return f"{self.color} {self.__class__.__name__} at ({self.x}, {self.y})"
    
    # strng representation of the piece for debugging (calls __str__)
    def __repr__(self) -> str:
        return self.__str__()
