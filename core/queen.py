#imports
from typing import Generator

from .piece import Piece
from .board import Board

# queen subclass - inherits from Piece
class Queen(Piece):

    # constructor
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        super().__init__(x, y, color, board)
        self.name = 'Queen'
        self.abbreviation = 'Q' if color else 'q'

    # gets all valid moves for the queen by sliding in all 8 directions
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (0, 1), (-1, 0), (0, -1)]
        return self.slide_all(directions)