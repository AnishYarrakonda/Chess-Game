#imports
import unittest

from core.board import Board


# Defines the TestIllegalAndTurns type.
class TestIllegalAndTurns(unittest.TestCase):
    # Handles test_cannot_move_wrong_side_piece operations.
    def test_cannot_move_wrong_side_piece(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertFalse(board.play_notation("a7a6"))

    # Handles test_illegal_move_rejected operations.
    def test_illegal_move_rejected(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertFalse(board.play_notation("e2e5"))

    # Handles test_pinned_piece_cannot_expose_king operations.
    def test_pinned_piece_cannot_expose_king(self) -> None:
        board = Board()
        board.load_fen("4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1")
        self.assertFalse(board.play_notation("Rd2"))


if __name__ == "__main__":
    unittest.main()
