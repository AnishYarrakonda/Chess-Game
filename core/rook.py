# imports
from typing import Generator

from .piece import Piece
from .board import Board

# rook subclass - inherits from Piece
class Rook(Piece):

    # constructor
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        super().__init__(x, y, color, board)
        self.name = 'Rook'
        self.abbreviation = 'R' if color else 'r'

    # gets all valid moves for the rook by sliding in orthogonal directions
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        return self.slide_all(directions)