from core.board import Board
from core.bishop import Bishop

def test_fen():
    board = Board()
    print(board.to_fen())
    assert board.to_fen() == '8/8/8/8/8/8/8/8'
    bishop = Bishop(0, 0, True, board)
    board.grid[0][0] = bishop
    print(board.to_fen())
    assert board.to_fen() == 'B7/8/8/8/8/8/8/8'