# imports
from typing import Generator

from .piece import Piece
from .board import Board

# king subclass - inherits from Piece
class King(Piece):

    # constructor
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        super().__init__(x, y, color, board)
        self.name = 'King'
        self.abbreviation = 'K' if color else 'k'

    # gets all valid moves for the king by checking adjacent squares
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        directions = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
        for dx, dy in directions:
            new_x = self.x + dx
            new_y = self.y + dy
            if self.board.in_bounds(new_x, new_y):
                piece = self.board.grid[new_x][new_y]
                if piece is None or piece.color != self.color:
                    yield (new_x, new_y)