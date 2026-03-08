#imports
import unittest

from core.board import Board


# Defines the TestSpecialMoves type.
class TestSpecialMoves(unittest.TestCase):
    # Handles test_en_passant_immediate_only operations.
    def test_en_passant_immediate_only(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        sequence = ["e2e4", "a7a6", "e4e5", "d7d5"]
        for move in sequence:
            self.assertTrue(board.play_notation(move))
        self.assertTrue(board.play_notation("e5d6"))

    # Handles test_en_passant_expires_after_one_turn operations.
    def test_en_passant_expires_after_one_turn(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        sequence = ["e2e4", "a7a6", "e4e5", "d7d5", "h2h3", "a6a5"]
        for move in sequence:
            self.assertTrue(board.play_notation(move))
        self.assertFalse(board.play_notation("e5d6"))

    # Handles test_promotion_default_to_queen operations.
    def test_promotion_default_to_queen(self) -> None:
        board = Board()
        board.load_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(board.play_notation("a7a8"))
        promoted = board.grid[0][0]
        self.assertIsNotNone(promoted)
        assert promoted is not None
        self.assertEqual(promoted.abbreviation, "Q")

    # Handles test_promotion_choice_knight operations.
    def test_promotion_choice_knight(self) -> None:
        board = Board()
        board.load_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(board.play_notation("a7a8N"))
        promoted = board.grid[0][0]
        self.assertIsNotNone(promoted)
        assert promoted is not None
        self.assertEqual(promoted.abbreviation, "N")


if __name__ == "__main__":
    unittest.main()
