from core.board import Board
from core.bishop import Bishop

def test_fen():
    board = Board()
    print(board.to_fen())
    assert board.to_fen() == '8/8/8/8/8/8/8/8 w - - 0 1'

    bishop = Bishop(0, 0, True, board)
    board.grid[0][0] = bishop
    print(board.to_fen())
    assert board.to_fen() == 'B7/8/8/8/8/8/8/8 w - - 0 1'

    board.load_fen('8/8/8/8/8/8/8/8 b KQkq e3 4 17')
    assert board.side_to_move is False
    assert board.castling_rights == 'KQkq'
    assert board.en_passant_target == (5, 4)
    assert board.halfmove_clock == 4
    assert board.fullmove_number == 17
    assert board.to_fen() == '8/8/8/8/8/8/8/8 b KQkq e3 4 17'
