import unittest

from core.board import Board


class TestSpecialMoves(unittest.TestCase):
    def test_en_passant_immediate_only(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        sequence = ["e2e4", "a7a6", "e4e5", "d7d5"]
        for move in sequence:
            self.assertTrue(board.play_notation(move))
        self.assertTrue(board.play_notation("e5d6"))

    def test_en_passant_expires_after_one_turn(self) -> None:
        board = Board()
        board.load_fen(Board.STARTING_FEN)
        sequence = ["e2e4", "a7a6", "e4e5", "d7d5", "h2h3", "a6a5"]
        for move in sequence:
            self.assertTrue(board.play_notation(move))
        self.assertFalse(board.play_notation("e5d6"))

    def test_promotion_default_to_queen(self) -> None:
        board = Board()
        board.load_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(board.play_notation("a7a8"))
        self.assertEqual(board.grid[0][0].abbreviation, "Q")

    def test_promotion_choice_knight(self) -> None:
        board = Board()
        board.load_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(board.play_notation("a7a8N"))
        self.assertEqual(board.grid[0][0].abbreviation, "N")


if __name__ == "__main__":
    unittest.main()
