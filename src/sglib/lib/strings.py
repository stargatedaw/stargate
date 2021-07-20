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


audio_viewer_widget_folders = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

Use this tab to browse your folders and files.
Drag and drop one file at a time onto the sequencer.
.wav and .aiff files are the only supported audio file format.
Click the 'Bookmark' button to save the current folder to your
bookmarks located on the 'Bookmarks' tab.
""")


audio_viewer_widget_papifx = _(
"""This tab allows you to set effects per-audio-file.
There will be exactly one instance of these effects per audio file.
Use this as a mixing aid for EQ, filter, etc... on a file.

The tab is only enabled when you have exactly one item selected,
the copy and paste buttons allow you to copy settings between
multiple items.""")

audio_viewer_widget_paifx = _(
"""This tab allows you to set effects per-audio-item.
The controls will be unique per instance of an audio file, and not
share between instances.  Use this to apply special effects to individual
instances of an audio file, such as panning hits around.

The tab is only enabled when you have exactly one item selected,
the copy and paste buttons allow you to copy settings between
multiple items.""")


timestretch_modes = _(
"""Modes:
None:  No stretching or pitch adjustment

Pitch affecting time:  Repitch the item, it will become
shorter at higher pitches, and longer at lower pitches

Time affecting pitch:  Stretch the item to the desired length, it will have
lower pitch at longer lengths, and higher pitch at shorter lengths

Rubberband:  Adjust pitch and time independently

Rubberband (formants): Same as Rubberband, but preserves formants

SBSMS:  Adjust pitch and time independently, also with the ability to
set start/end pitch/time differently

Paulstretch:  Mostly for stretching items very long, creates a very smeared,
atmospheric sound""")


transport = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

This is the transport, use this control to start/stop
playback or recording.
You can start or stop playback by pressing spacebar
The panic button sends a note-off event on every note to every plugin,
use this when you get a stuck note.
""")


avconv_error = _(
"""Please ensure that avconv(or ffmpeg) and lame are installed, can't
open mp3 converter dialog.
Check your normal sources for packages or visit:

http://lame.sourceforge.net
http://libav.org

Can't find {}""")

export_format = _(
"""File is exported to 32 bit .wav at the sample rate your audio
interface is running at.
You can convert the format using the Menu->Tools dialogs""")

pitchbend_dialog = _(
"""Pitchbend values are in semitones.

Use this dialog to add points with precision,or double-click on
the editor to add points.""")

PianoRollEditor = _("""\
Click 'Menu->Show Tooltips' in the transport to disable these tooltips

Click+drag to draw notes
CTRL+click+drag to marquee select multiple items
SHIFT+click+drag to delete notes
CTRL+ALT+click+drag-up/down to adjust the velocity of selected notes
CTRL+SHIFT+click+drag-up/down to create a velocity curve for the selected notes
Press the Delete button on your keyboard to delete selected notes
To edit velocity, press the menu button and select
the Velocity->Dialog... action
Click and drag the note end to change the length of selected notes
To edit multiple items as one logical item, select multiple items in the sequence
editor and right-click + 'Edit Selected Items as Group'
The Quantize, Transpose and Velocity actions in the menu button open dialogs
to manipulate the selected notes (or all notes if none are selected)\
""")


AudioItemSeq = _("""\
Drag audio files from the file browser onto here.

Click 'Menu->Show Tooltips' in the transport to disable these tooltips
""")

AudioSeqItem = _("""\
Right click on an audio item to see the various tools and actions available.

Click and drag selected to move.

Select 1+ items, CTRL+click+drag up/down/left/right to copy selected items
Select 1+ items, ALT+SHIFT+Click and drag up/down:
    Modify the volume of the file.  This is useful for mixing, as it modifies
    the volume of every instance of the file in the entire project.
Select 1+ items, CTRL+ALT+Click and drag up/down:
    Modify the volume of selected items.  Different audio items in the
    same sequencer item can have different volumes using this technique.
Select 1+ items, CTRL+SHIFT+Click and drag up/down:
    Create a volume line for the selected items.  For example, you have the
    same kick drum sample repeated 4 times in an item, one beat apart from
    each other.  Select all of them, perform this mouse gesture by clicking
    on the first one and dragging down.  The respective values might be
    -9dB, -6dB, -3dB, 0dB, getting progressively louder.
See the menu button above for additional actions""")

multiple_instances_warning = _("""\
Detected that there are instances of the Stargate
audio engine already running.
This could mean that you already have Stargate running, if so you
should click 'Cancel' and close the other instance.

This could also mean that for some reason the engine didn't properly
terminate from another session.  If so, click 'OK' to kill the
other process(es)""")

routing_graph = _("""\
This shows the audio, sidechain and MIDI routing of each track.

Click above the track to connect/disconnect a track's output to
the destination track behind it (higher track number).

Click below to connect a track to the track in front of it
(lower track number).

Click to route audio to the input of a track, which will appear as
a white line.

CTRL+click to connect/disconnect to the sidechain input of the track,
which will appear as a red line.

SHIFT+click to connect/disconnect to the MIDI input of the track,
which will appear as a blue line.

Creating feedback loops is not supported, you will receive an error
message if an attempted connection creates feedback.
"""
)

troubleshooting = _("""\
<h3>Drop-outs or Xruns:</h3>

<p>Xruns are usually caused by CPU power management throttling the CPU clock
frequency too aggressively, especially if you are using a laptop.  Other
causes are using an older or slower CPU in a CPU intensive project, or
possibly (but probably not) bad audio drivers.</p>

<p>Some PCs may just be able to force the CPU
governor to "Performance" mode, others may have to disable power management
features in the BIOS.  Many laptops don't expose the ability to turn off
these features in the BIOS.</p>

<p>Unfortunately, there is no one-size-fits-all
solution, as different generations of Intel and AMD processors use different
CPU frequency drivers and offer different power saving features and different
BIOS.</p>

<p>Others causes could be using a Jack audio device, ALSA is the preferred
back-end for Stargate (and does not require a special real-time
Linux kernel to achieve decent latency)</p>

<p>If you only experience Xruns immediately after starting Stargate, you
may want to try adding "vm.swappiness=0" to /etc/sysctl.conf and
rebooting</p>

<h3>My microphone doesn't work</h3>

<p>On some interfaces (such as the Apogee One), you may need to open the
terminal, type the command "alsamixer", and select your interface and
set the input source to something like '48v ext. mic.', and/or adjust the
microphone volume.</p>

<p>You may also need to set the number of inputs on the
"Audio In" tab of the Menu->File->HardwareSettings... dialog</p>

<h3>The UI is sluggish in a large project</h3>

<p>If using an Nvidia or AMD graphics card, you should probably try
installing the proprietary driver for you card.  In Ubuntu, with an
AMD card, for example: sudo apt-get install fglrx.</p>

<h3>The playback cursor doesn't move after pressing the play button</h3>

<p>This is <i>usually</i> caused by selecting an incorrect audio device,
such as the "default" audio device.  Ensure that you have selected the
correct device from Menu->File->HardwareSettings...</p>
"""
)

track_panel = _("""\
This is the track panel.  Each track has a name textbox, solo & mute
buttons, and a dropdown menu.

The dropdown menu contains the track plugins (instrument and effects),
the track sends and their mixer plugins, and controls for selecting
parameters for automation.  For a global view of track sends, see the
routing tab.

A track can be any or all of audio, MIDI, send or bus, at the same time.
Instrument plugins can be placed before or after effect plugins, and
will pass-through any audio from items or sends.
"""
)

PluginRack = _("""\
This is the plugin rack.  Select the track you wish to edit from the
track combobox, and select it's plugins within the rack.
""")

Mixer = _("""\
This is the mixer.  Route tracks between each other and the
main track using the "Routing" tab.  When you create a route,
it will show a channel on the mixer, where you can select a
mixer plugin to control the channel with.
""")
