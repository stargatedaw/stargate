
def mfx_set_tooltip(knobs, idx: int):
    tooltips = MULTIFX_TOOLTIPS.get(idx, [])
    if len(knobs) > len(tooltips):
        tooltips += (len(knobs) - len(tooltips)) * ('',)
    for knob, tooltip in zip(knobs, tooltips):
        knob.control.setToolTip(tooltip)

MFX_TOOLTIPS_FILTER = (
    'Filter cutoff frequency',
    'Filter resonance',
    '',
)
MFX_TOOLTIP_DISTORTION = (
     'Input gain, higher values result in a more distorted sound',
     'Dry/Wet, higher values result in more distortion',
     'Output gain, compensate for increased volume by reducing out gain',
)

MULTIFX_TOOLTIPS = {
    0: ('', '', ''),  # Off
    1: MFX_TOOLTIPS_FILTER, # LP2
    2: MFX_TOOLTIPS_FILTER, # LP4
    3: MFX_TOOLTIPS_FILTER, # HP2
    4: MFX_TOOLTIPS_FILTER, # HP4
    5: MFX_TOOLTIPS_FILTER, # BP2
    6: MFX_TOOLTIPS_FILTER, # BP4
    7: MFX_TOOLTIPS_FILTER, # Notch2
    8: MFX_TOOLTIPS_FILTER, # Notch2
    9: (  # EQ
        'The EQ band frequency to increase or decrease volume at',
        'EQ bandwidth',
        'EQ gain',
    ),
    10: MFX_TOOLTIP_DISTORTION,  # Distortion
    11: (  # Comb filter
        'Filter frequency',
        'Filter amount, higher values result in more phasing sound',
        '',
    ),
    12: (  # Amp/panner
        'Pan the signal left or right',
        'Gain, adjust the volume',
         '',
    ),
    13: (  # Limiter
         'Limiter threshold, lower values result in a more compressed sound',
         'Ceiling, autogain will prevent the output from exceeding this value',
         'Release, higher values result in less compression',
    ),
    14: MFX_TOOLTIP_DISTORTION,  # Saturator
    15: (
         'Vowel, this knob selects the vowel to use',
         'Dry/wet control',
         '',
    ),
    16: (  # Chorus
        'Rate, the speed of the chorus LFO',
        'Dry/wet control',
        'Fine control of the chorus LFO rate',
    ),
    17: (  # Glitch
        'The frequency of the effect',
        'The length of the glitch buffer',
         'Dry/wet control',
    ),
    18: (  # RingMod
         'Pitch, the frequency of the oscillator',
         'Dry/wet control',
         '',
    ),
    19: (  # LoFi
         'The number of bits to reduce the audio to',
         '',
         '',
    ),
    20: (  # S&H
         'Sample hold time.  Lower values result in more distortion',
         'Dry/wet control',
         '',
    ),
    21: (  # LP2-Dry/Wet
         'Filter cutoff frequency',
         'Filter resonance',
         'Dry/wet control',
    ),
    22: (  # HP2-Dry/Wet
         'Filter cutoff frequency',
         'Filter resonance',
         'Dry/wet control',
    ),
    23: (  # Monofier
         'Pan the combined mono signal left or right',
         'Volume, adjust the gain of the combined signal',
         '',
    ),
    24: (  # LP<-->HP
         'Filter cutoff frequency',
         'Filter resonance',
         'Fade from lowpass to highpass',
    ),
    25: (  # Growl filter
         'Vowel, fade between different filter vowels',
         'Dry/wet control',
         'The growl type',
    ),
    26: MFX_TOOLTIPS_FILTER,  # LP Screech
    27: (  # Metal comb
         'Filter frequency',
         'Filter amount',
         'Unison detune, higher values result n a thicker sound',
    ),
    28: (  # Notch4 Dry/wet
         'Filter frequency',
         'Filter resonance',
         'Dry/wet control',
    ),
    29: (  # Foldback distortion
         'Threshold, lower values result in more distortion',
         'Input gain, higher values result in more distortion',
         'Dry/wet control',
    ),
    30: (  # Notch spread
         'Filter frequency',
         'Filter resonance',
         'Filter spread, in semitones',
    ),
    31: (  # DC Offset
         '',
         '',
         '',
    ),
    32: (  # BP spread
         'Filter frequency',
         'Filter resonance',
         'Filter spread, in semitones',
    ),
    33: (  # Phaser static
         'Phaser frequency',
         'Dry/wet control',
         'Phaser feedback, higher values result in more phasing',
    ),
    34: (  # Flanger static
         'Flanger frequency',
         'Dry/wet control',
         'Flanger feedback, higher values result in more flanging',
    ),
    35: (  # Soft clipper
         'Threshold, lower values result in more distortion',
         'Shape, lower values result in harder distortion',
         'Output gain, compensate for changes in volume',
    ),
}
