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


audio_viewer_widget_papifx = _("""\
This tab allows you to set effects per-audio file.  There will be exactly one
instance of these effects per audio file.  Use this as a mixing aid for EQ,
filter, etc... on a file.""")

audio_viewer_widget_paifx = _("""\
This tab allows you to set effects per-audio-item.  The effects will be unique
per instance of an audio file, and not share between instances.""")

timestretch_modes = {
    0:  'No stretching or pitch adjustment',
    1:  (
        'Repitch the item, it will become shorter at higher pitches, and '
        'longer at lower pitches'
    ),
    2:  (
        'Stretch the item to the desired length, it will have lower pitch '
        'at longer lengths, and higher pitch at shorter lengths'
    ),
    3:  'Adjust pitch and time independently',
    4: (
        'Same as Rubberband, but preserves formants when pitch shifting.  '
        'Useful on vocal materials, an auto-tune type of pitch shifting'
    ),
    5: (
        'Adjust pitch and time independently, also with the ability to '
        'set start/end pitch/time differently'
    ),
    6:  (
        'Mostly for stretching items very long, creates a very smeared, '
        'atmospheric sound.  Useful for creative reverb-like effects and '
        'soundscapes'
    ),
    7: (
        'A good timestretching algorithm for many types of materials. '
        'Optimized for full pieces of music'
    ),
    8: (
        'A good timestretching algorithm for many types of materials. '
        'Optimized for speech'
    ),
}

avconv_error = _(
"""\
Please ensure that ffmpeg (or avconv) and lame are installed.
cannot open mp3 converter dialog.
Check your normal sources for packages or visit:

http://lame.sourceforge.net
http://ffmpeg.org

Cannot find {}""")

export_format = _(
"""File is exported to 32 bit .wav at the sample rate your audio
interface is running at.
You can convert the format using the Menu->Tools dialogs""")

pitchbend_dialog = _("""\
Pitchbend values are in semitones.  Use this dialog to add points with
precision,or double-click on the editor to add points.""")

PianoRollEditor = f"""
Edit MIDI notes.  See the "Parameter" combobox, the menu button and the mouse
tools in the transport panel. Draw notes holding {KEY_ALT} to move instead of
change length when moving the mouse.
"""


AudioItemSeq = _("""\
Item editor for audio.  Each sequencer item can contain multiple
audio items in addition to MIDI.  Drag audio files from the file browser
onto here.  See the menu button, the right click audio item menu, and the
various hints for the items, actions and handles.
""")

AudioSeqItem = _(f"""
Audio item, represents an audio file.  Right click: actions menu.
{KEY_CTRL}+{KEY_ALT}+drag: modify vol. of individual items, CTRL+SHIFT+drag
selected items: item vol. curve, {KEY_ALT}+SHIFT+drag: modify vol of all
instances of the file in all items.  {KEY_CTRL}+click+drag: duplicate items,
{KEY_ALT}+click: multi-select.
"""
)

multiple_instances_warning = _("""\
Detected that there are instances of the Stargate audio engine already running.
This could mean that you already have Stargate running, if so you
should click 'Cancel' and close the other instance.

This could also mean that for some reason the engine did not properly
terminate from another session.  If so, click 'OK' to kill the
other process(es)""")

routing_graph = f"""\
Route audio and MIDI between tracks.  Audio (click),
sidechain({KEY_CTRL}+click) and MIDI(SHIFT+click). Click below the destination
to route to lower numbered tracks, click above for higher numbered tracks.
Lower numbers are towards the top left, and higher numbers are towards the
bottom right. Double click a track to open plugins
"""

track_panel_dropdown = _("""\
The dropdown menu contains a shortcut to the track plugins (instrument and
effects), and controls for selecting parameters for automation.  For a global
view of track sends, see the routing tab.""")

"""
A track can be any or all of audio, MIDI, send or bus, at the same time.
Instrument plugins can be placed before or after effect plugins, and
will pass-through any audio from items or sends.
"""

ENGINE_MON = """\
Shows CPU and memory percentage.  Note that the CPU usage is a max of the
cores that are in use, not based on the average of CPU load and available
logical cores, which is less useful.
"""

NO_AUDIO_INPUTS_INSTRUCTIONS = """\
No audio inputs available.  If you are using an audio device with inputs, press
the Hardware Settings button and ensure that the audio inputs control is set to
a number greater than 0.
"""

