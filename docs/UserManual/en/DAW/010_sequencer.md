# Sequencer
The sequencer allows you to create items containing audio, notes, MIDI CCs and
MIDI pitchbend (PB), and arrange them into a song.  Using the mouse tools
on the transport to draw, select, erase and split sequencer items.

## Copying Items
There are multiple ways to copy items, the preferred method depends on how
many items you need to copy

- Select one or more items using the selection mouse tool,
  CTRL+left\_click and drag to copy
- Right-click on the sequencer header, select `Set region start`,
  `Set region end`, `Copy region` and `Insert region` to duplicate a region.

## Tracks
Each track corresponds to a plugin rack on the `Plugin Racks` tab.  The track
that an item goes in will determine which plugin rack processes it's audio
and MIDI events.  All items and all plugin racks can process audio and MIDI
at the same time.

## Sequencer Header
The sequencer header can be clicked on to set the playback cursor position.
Right clicking allows various "markers" to be set:
- Region start/end, used for offline rendering and looping
- Text marker, write a note on the timeline about a particular point in
  the song
- Tempo marker or tempo range, set the tempo for the song at that point

## Songs List
Stargate allows you to have more than one song in a project.  In addition to
the default song, you can add additional songs for uses such as:
- Sound design scratchpad, create small sections to be rendered as audio and
  imported into the main song
- Alternative songs

All songs share the same plugin racks, and same item pool.  Changes made to
the same item in different songs will be reflected in all songs.

## Items
A sequencer item can combine multiple audio items, notes, CCs and Pitchbend
events into a single item.  This design really shines when creating your
own drum patterns, for example.

### Takes
When you copy and item in Stargate, it is the same item, and changes to one
copy affect all copies of items with that name.  To make changes to an item
without affecting existing copies, right-click and create a new take.

