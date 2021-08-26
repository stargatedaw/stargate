from sglib.models import theme

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

