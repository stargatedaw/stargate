# Mixer
The mixer allows to you mix your audio and adjust the volume and pan of each
channel.  For each audio send defined on the `Routing` tab, there will be
a slot created for a mixer plugin on the mixer.

# Mixer Plugins
In Stargate, the mixer uses plugins to provide mixer channel functionality.
Presently, the 2 mixer plugins are `Simple Fader` and `SG Channel`, although
in the future we may offer more mixer plugins.

The mixer plugin is the last plugin in a plugin rack.  If you want a
pre-channel, you can add a mixer plugin as the first plugin in the plugin
rack, but it will only be visible in the plugin rack and not the mixer.
