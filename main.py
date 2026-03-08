from tests.test_fen import test_fen
from tests.test_checks import test_in_check_detection, test_legal_moves_filter_pinned_rook

if __name__ == "__main__":
    test_fen()
    test_in_check_detection()
    test_legal_moves_filter_pinned_rook()
    print("All tests passed!")
