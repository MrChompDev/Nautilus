import pytest


class TestExample:
    """Test suite."""

    def test_basic(self):
        assert True

    def test_addition(self):
        assert 1 + 1 == 2

    @pytest.mark.parametrize('input,expected', [
        ('hello', 5),
        ('', 0),
        ('world', 5),
    ])
    def test_length(self, input, expected):
        assert len(input) == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
