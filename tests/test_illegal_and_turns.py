import unittest

from core.board import Board


class TestIllegalAndTurns(unittest.TestCase):
    def test_cannot_move_wrong_side_piece(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertFalse(board.play_notation("a7a6"))

    def test_illegal_move_rejected(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertFalse(board.play_notation("e2e5"))

    def test_pinned_piece_cannot_expose_king(self) -> None:
        board = Board()
        board.load_fen("4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1")
        self.assertFalse(board.play_notation("Rd2"))


if __name__ == "__main__":
    unittest.main()
