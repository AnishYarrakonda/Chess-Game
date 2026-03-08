from core.board import Board


def test_in_check_detection():
    board = Board()
    board.load_fen("4k3/8/8/8/4r3/8/8/4K3 w - - 0 1")
    assert board.in_check(True) is True
    assert board.in_check(False) is False


def test_legal_moves_filter_pinned_rook():
    board = Board()
    board.load_fen("k3r3/8/8/8/8/8/4R3/4K3 w - - 0 1")

    pinned_rook = board.grid[6][4]
    assert pinned_rook is not None

    legal_moves = set(board.get_legal_moves(pinned_rook))
    assert legal_moves == {(5, 4), (4, 4), (3, 4), (2, 4), (1, 4), (0, 4)}
