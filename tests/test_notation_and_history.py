#imports
import unittest

from core.board import Board


# Defines the TestNotationAndHistory type.
class TestNotationAndHistory(unittest.TestCase):
    # Handles test_san_and_uci_inputs operations.
    def test_san_and_uci_inputs(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertTrue(board.play_notation("e4"))
        self.assertTrue(board.play_notation("e7e5"))
        self.assertTrue(board.play_notation("Nf3"))
        self.assertEqual(board.move_notation_history[:3], ["e4", "e5", "Nf3"])

    # Handles test_illegal_notation_returns_false operations.
    def test_illegal_notation_returns_false(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertFalse(board.play_notation("Qa9"))

    # Handles test_undo_restores_previous_state operations.
    def test_undo_restores_previous_state(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        self.assertTrue(board.play_notation("e2e4"))
        fen_after = board.to_fen()
        self.assertTrue(board.undo_move())
        self.assertEqual(board.to_fen(), Board.STARTING_FEN)
        self.assertNotEqual(board.to_fen(), fen_after)


if __name__ == "__main__":
    unittest.main()
