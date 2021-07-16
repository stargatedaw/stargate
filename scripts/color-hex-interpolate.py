#!/usr/bin/env python3

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'foreground',
        help="The foreground color",
    )
    parser.add_argument(
        'background',
        help="The background color",
    )
    parser.add_argument(
        'opacity',
        type=float,
        help=(
            "The opacity of the foreground color, 0.0(tranparent)-1.0(opaque)"
        ),
    )
    return parser.parse_args()

def interpolate(
    foreground,
    background,
    opacity,
):
    if foreground.startswith('#'):
        foreground = foreground[1:]
    if background.startswith('#'):
        background = background[1:]
    for x in (foreground, background):
        assert len(x) == 6, f"Invalid hex color {x}"
    assert opacity >= 0. and opacity <= 1., opacity
    result = ""
    for i in range(3):
        fg = float(int(foreground[i*2:(i*2)+2], 16))
        bg = float(int(background[i*2:(i*2)+2], 16))
        color = ((fg - bg) * opacity) + bg
        result += hex(int(color))[2:]
    return result

if __name__ == "__main__":
    args = parse_args()
    print(interpolate(**args.__dict__))
