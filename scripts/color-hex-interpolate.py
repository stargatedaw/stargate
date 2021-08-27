#!/usr/bin/env python3

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'start_color',
        help="The start_color color",
    )
    parser.add_argument(
        'end_color',
        help="The end_color color",
    )
    parser.add_argument(
        '--pos',
        default=0.5,
        dest='pos',
        type=float,
        help='The position to interpolate to.  Ignored if --count > 1',
    )
    parser.add_argument(
        '--count',
        default=1,
        dest='count',
        type=int,
        help=(
            "The number of colors to return, evenly spaced interpolations"
        ),
    )
    return parser.parse_args()

def interpolate(
    start_color,
    end_color,
    count,
    pos,
):
    if start_color.startswith('#'):
        start_color = start_color[1:]
    if end_color.startswith('#'):
        end_color = end_color[1:]
    for x in (start_color, end_color):
        assert len(x) == 6, f"Invalid hex color {x}"
    if count == 1:
        print(_interpolate(start_color, end_color, pos))
    elif count == 2:
        print(start_color)
        print(end_color)
    else:
        pos_step = 1. / float(count - 1)
        _pos = pos_step
        _print(start_color)
        for i in range(count - 2):
            _print(_interpolate(start_color, end_color, _pos))
            _pos += pos_step
        _print(end_color)

def _print(_str):
    print(f"#{_str}")

def _interpolate(
    start_color,
    end_color,
    pos,
):
    assert pos >= 0. and pos <= 1., pos
    result = ""
    for i in range(3):
        bg = float(int(start_color[i*2:(i*2)+2], 16))
        fg = float(int(end_color[i*2:(i*2)+2], 16))
        color = ((fg - bg) * pos) + bg
        result += hex(int(color))[2:]
    return result

if __name__ == "__main__":
    args = parse_args()
    interpolate(**args.__dict__)
