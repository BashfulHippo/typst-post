import pytest

from typst_post.pages import parse_page_list


def test_single_pages():
    assert parse_page_list("4,1,2", 8) == [3, 0, 1]


def test_forward_and_backward_ranges():
    assert parse_page_list("1-3", 8) == [0, 1, 2]
    assert parse_page_list("8-5", 8) == [7, 6, 5, 4]


def test_mixed():
    assert parse_page_list("2,4-5,1", 5) == [1, 3, 4, 0]


def test_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        parse_page_list("9", 8)
    with pytest.raises(ValueError, match="out of range"):
        parse_page_list("0", 8)


def test_invalid_token():
    with pytest.raises(ValueError, match="invalid page number"):
        parse_page_list("2,x", 8)
    with pytest.raises(ValueError, match="empty page token"):
        parse_page_list("1,,2", 8)
