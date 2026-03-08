#imports
import unittest

from core.board import Board


# Defines the TestCastling type.
class TestCastling(unittest.TestCase):
    # Handles test_white_kingside_castle operations.
    def test_white_kingside_castle(self) -> None:
        board = Board()
        board.load_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        self.assertTrue(board.play_notation("O-O"))
        self.assertEqual(board.to_fen().split()[0], "r3k2r/8/8/8/8/8/8/R4RK1")

    # Handles test_white_queenside_castle operations.
    def test_white_queenside_castle(self) -> None:
        board = Board()
        board.load_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        self.assertTrue(board.play_notation("O-O-O"))
        self.assertEqual(board.to_fen().split()[0], "r3k2r/8/8/8/8/8/8/2KR3R")

    # Handles test_black_kingside_castle operations.
    def test_black_kingside_castle(self) -> None:
        board = Board()
        board.load_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
        self.assertTrue(board.play_notation("O-O"))
        self.assertEqual(board.to_fen().split()[0], "r4rk1/8/8/8/8/8/8/R3K2R")

    # Handles test_black_queenside_castle operations.
    def test_black_queenside_castle(self) -> None:
        board = Board()
        board.load_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
        self.assertTrue(board.play_notation("O-O-O"))
        self.assertEqual(board.to_fen().split()[0], "2kr3r/8/8/8/8/8/8/R3K2R")

    # Handles test_castling_through_check_is_illegal operations.
    def test_castling_through_check_is_illegal(self) -> None:
        board = Board()
        board.load_fen("4kr2/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        self.assertFalse(board.play_notation("O-O"))

    # Handles test_castling_while_in_check_is_illegal operations.
    def test_castling_while_in_check_is_illegal(self) -> None:
        board = Board()
        board.load_fen("4r1k1/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        self.assertFalse(board.play_notation("O-O"))


if __name__ == "__main__":
    unittest.main()
