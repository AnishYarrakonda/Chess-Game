#imports
from typing import Generator

from .piece import Piece
from .board import Board

# bishop subclass - inherits from Piece
class Bishop(Piece):

    # constructor
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        super().__init__(x, y, color, board)
        self.name = 'Bishop'
        self.abbreviation = 'B' if color else 'b'

    # gets all valid moves for the bishop by sliding in diagonal directions
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self.slide_all(directions)