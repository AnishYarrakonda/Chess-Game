#imports
import unittest

from core.board import Board


# Defines the TestFenState type.
class TestFenState(unittest.TestCase):
    # Handles test_starting_fen_round_trip operations.
    def test_starting_fen_round_trip(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertEqual(board.to_fen(), Board.STARTING_FEN)

    # Handles test_full_fen_fields_round_trip operations.
    def test_full_fen_fields_round_trip(self) -> None:
        fen = "r3k2r/8/8/8/8/8/8/R3K2R b KQkq e3 17 42"
        board = Board()
        board.load_fen(fen)
        self.assertEqual(board.to_fen(), fen)


if __name__ == "__main__":
    unittest.main()
