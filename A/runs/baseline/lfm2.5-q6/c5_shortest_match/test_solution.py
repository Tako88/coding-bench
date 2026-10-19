import sys
sys.path.insert(0, '.')
from solution import shortest_prefix_match

def test_examples():
    assert shortest_prefix_match('abc', 'abcdef') == 3
    assert shortest_prefix_match('a*c', 'abcde') == 3
    assert shortest_prefix_match('*', 'abc') == 0
    assert shortest_prefix_match('*', '') == 0
    assert shortest_prefix_match('a*', 'a') == 1
    assert shortest_prefix_match('*b', 'aaab') == 4
    assert shortest_prefix_match('**b', 'ab') == 2
    assert shortest_prefix_match('{ab,cd}', 'cdx') == 2
    assert shortest_prefix_match('{a,ab}c', 'abc') == 3
    assert shortest_prefix_match('{*,a}b', 'ab') == 2
    assert shortest_prefix_match('{,a}b', 'ab') == 2
    assert shortest_prefix_match('{}', 'ab') == 0
    assert shortest_prefix_match('{a,\\{b}c', '{bcd') == 3
    assert shortest_prefix_match('{\\{a,b}', '{a') == 2
    assert shortest_prefix_match('a?c', 'abcd') == 3
    assert shortest_prefix_match('a\\*b', 'a*bc') == 3
    assert shortest_prefix_match('a', '') == -1
    assert shortest_prefix_match('abc', 'ab') == -1

def test_errors():
    try:
        shortest_prefix_match('a\\', 'a')
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        shortest_prefix_match('{a,b', 'ab')
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        shortest_prefix_match('a}b', 'ab')
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        shortest_prefix_match('{a,{b}c', 'abc')
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        shortest_prefix_match('{a{b}', 'a{b')
        assert False, "Expected ValueError"
    except ValueError:
        pass

def test_edge_cases():
    # Empty pattern matches empty text
    assert shortest_prefix_match('', '') == 0
    assert shortest_prefix_match('', 'abc') == 0
    # Empty group
    assert shortest_prefix_match('{}', 'ab') == 0
    # Question mark
    assert shortest_prefix_match('?', 'a') == 1
    assert shortest_prefix_match('?', '') == -1
    # Star at end matching single char
    assert shortest_prefix_match('a*', 'a') == 1
    # Multiple stars
    assert shortest_prefix_match('***', 'x') == 0
    # Group with empty alternative
    assert shortest_prefix_match('{a,}', 'a') == 1
    assert shortest_prefix_match('{a,}', '') == 0

if __name__ == '__main__':
    test_examples()
    test_errors()
    test_edge_cases()
    print("All tests passed!")
