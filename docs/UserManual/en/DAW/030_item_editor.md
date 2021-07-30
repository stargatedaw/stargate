# Item Editor
To open an item, create one in the sequencer using the drawing mouse tool and
double-click on it.  Items can include one or more audio, note, MIDI CC or MIDI
pitchbend (PB) events.

## Audio
Create an audio item by dragging a file from the file browser to the item
canvas.  There is a bookmarks tab where you can bookmark your favorite sample
folders.  Use the item handles to change the start, end, fades and stretching
parameters.  There are many options available in the right-click context menu.

### Per-File and Per-Item Effects
Each audio item can have it's own effects.  Use per-file effects as a mixing
aid, to add EQ, filtering and panning to each file.  Setting it to one file
will set it for all instances of that file in the project.

Use per-item effects when you want an effect to only apply to a single instance
of a file.  For example, panning individual hits around the stereo field.

### Mixing
In addition to per-file effects, you can also set per-file volume directly
by ALT+SHIFT+drag-up/down to change the volume of a file.

## Notes
This is a standard piano roll editor.  Draw notes using the mouse tools.  Note
that velocity is modified using mouse modifiers, see the tooltip documentation
for all available options for modifying velocity.

## CC/PB
These editors are very similar.  To set a plugin control to a CC, go to the
plugin rack, right click on the knob, and assign or learn a CC number.
