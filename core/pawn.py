# imports
from typing import Generator

from .piece import Piece
from .board import Board

# pawn subclass - inherits from Piece
class Pawn(Piece):

    # constructor
    def __init__(self, x: int, y: int, color: bool, board: Board) -> None:
        super().__init__(x, y, color, board)
        self.name = 'Pawn'
        self.abbreviation = 'P' if color else 'p'

    # gets valid moves for the pawn, including forward moves and captures
    def get_valid_moves(self) -> Generator[tuple[int, int], None, None]:
        direction = 1 if self.color else -1
        start_row = 1 if self.color else 6

        # forward move
        new_x = self.x + direction
        if self.board.in_bounds(new_x, self.y) and self.board.grid[new_x][self.y] is None:
            yield (new_x, self.y)

            # double move from starting position
            if self.x == start_row:
                new_x2 = self.x + 2 * direction
                if self.board.in_bounds(new_x2, self.y) and self.board.grid[new_x2][self.y] is None:
                    yield (new_x2, self.y)

        # captures
        for dy in [-1, 1]:
            new_y = self.y + dy
            if self.is_opponent_piece(new_x, new_y):
                yield (new_x, new_y)