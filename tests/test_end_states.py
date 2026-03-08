#imports
import unittest

from core.board import Board


# Defines the TestEndStates type.
class TestEndStates(unittest.TestCase):
    # Handles test_checkmate_detection operations.
    def test_checkmate_detection(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        for move in ["f2f3", "e7e5", "g2g4", "Qh4#"]:
            self.assertTrue(board.play_notation(move))
        self.assertTrue(board.is_checkmate())

    # Handles test_stalemate_detection operations.
    def test_stalemate_detection(self) -> None:
        board = Board()
        board.load_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        self.assertTrue(board.is_stalemate())

    # Handles test_fifty_move_rule operations.
    def test_fifty_move_rule(self) -> None:
        board = Board()
        board.load_fen("8/8/8/8/8/8/8/K6k w - - 100 1")
        self.assertTrue(board.is_draw_by_fifty_move_rule())

    # Handles test_threefold_repetition operations.
    def test_threefold_repetition(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        loop = ["g1f3", "g8f6", "f3g1", "f6g8"]
        for _ in range(2):
            for move in loop:
                self.assertTrue(board.play_notation(move))
        self.assertTrue(board.is_draw_by_threefold_repetition())

    # Handles test_insufficient_material operations.
    def test_insufficient_material(self) -> None:
        board = Board()
        board.load_fen("8/8/8/8/8/8/8/K6k w - - 0 1")
        self.assertTrue(board.is_draw_by_insufficient_material())


if __name__ == "__main__":
    unittest.main()
