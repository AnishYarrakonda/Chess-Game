#imports
import tempfile
import unittest
from pathlib import Path

from game.game import ChessGame


# Defines the TestGameSaveLoadAnalysis type.
class TestGameSaveLoadAnalysis(unittest.TestCase):
    # Handles test_save_load_and_navigation operations.
    def test_save_load_and_navigation(self) -> None:
        game = ChessGame()
        for move in ["e2e4", "e7e5", "g1f3", "b8c6"]:
            self.assertTrue(game.play(move))

        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "game.json"
            game.save(save_path)
            loaded = ChessGame.load(save_path)

            self.assertEqual(loaded.timeline, game.timeline)
            self.assertEqual(loaded.timeline_index, game.timeline_index)

            self.assertTrue(loaded.step_backward())
            self.assertTrue(loaded.step_forward())
            self.assertFalse(loaded.step_forward())

    # Handles test_continue_from_loaded_game operations.
    def test_continue_from_loaded_game(self) -> None:
        game = ChessGame()
        for move in ["e2e4", "e7e5", "g1f3", "b8c6"]:
            self.assertTrue(game.play(move))

        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "game.json"
            game.save(save_path)
            loaded = ChessGame.load(save_path)
            self.assertTrue(loaded.play("f1b5"))
            self.assertEqual(loaded.timeline_index, len(loaded.timeline) - 1)

    # Handles test_branch_after_stepping_back_truncates_future operations.
    def test_branch_after_stepping_back_truncates_future(self) -> None:
        game = ChessGame()
        for move in ["e2e4", "e7e5", "g1f3", "b8c6"]:
            self.assertTrue(game.play(move))

        self.assertTrue(game.step_backward())
        old_len = len(game.timeline)
        self.assertTrue(game.play("d7d6"))
        self.assertLess(len(game.timeline), old_len + 1)
        self.assertEqual(game.timeline_index, len(game.timeline) - 1)


if __name__ == "__main__":
    unittest.main()
