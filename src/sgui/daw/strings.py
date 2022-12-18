"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

from sglib.lib.translate import _
from sglib.lib.util import KEY_CTRL, KEY_ALT

sequencer = _("""\
Sequencer contains tracks, items, and automation. Use the mouse tools in
the transport to edit sequencer items. Right click on items or the
timeline for actions.  All items/tracks can contain audio and MIDI.""")

sequencer_item = f"""
Right click to see available actions.  See mouse tools in transport.
Click+drag selected to move.  {KEY_CTRL}+drag to copy selected items.
Double-click to edit.  {KEY_ALT}+click to multi-select
"""

