# imports
from typing import Generator

from .piece import Piece
from .board import Board

# knight subclass - inherits from Piece
class Knight(Piece):

    # constructor
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        super().__init__(x, y, color, board)
        self.name = 'Knight'
        self.abbreviation = 'N' if color else 'n'

    # gets all valid moves for the knight by checking all 8 possible L-shaped moves
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        directions = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dx, dy in directions:
            new_x = self.x + dx
            new_y = self.y + dy
            if self.board.in_bounds(new_x, new_y) and not self.is_friendly_piece(new_x, new_y):
                yield (new_x, new_y)