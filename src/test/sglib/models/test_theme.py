from sglib.models import theme
import pytest

SCALER = theme.UIScaler(
    2000.,
    1000.,
    2000.,
    1000.,
)

def test_ui_scaler_pct_to_px():
    for args, expected in (
        ((10.,), 100),
        ((50., 'w'), 1000),
    ):
        result = SCALER.pct_to_px(*args)
        assert result == expected, (result, expected)

def test_hex_color():
    for color in (
        '#ccc',
        '#cccccc',
        '#cccccccc',
        '#000000',
        '#FFFFFF',
        '#ffffff',
    ):
        theme.hex_color_assert(color)

def test_hex_color_raises():
    for color in (
        '#33333g',
        '#11cccccccc',
        '#ZZZZZZ',
    ):
        with pytest.raises(ValueError):
            theme.hex_color_assert(color)

