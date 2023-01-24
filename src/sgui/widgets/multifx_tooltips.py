class MultiFXInfo:
    def __init__(
        self,
        index: int,
        tooltip: str,
    ):
        self.index = index
        self.tooltip = tooltip

MULTIFX_INFO = {
    "Off": MultiFXInfo(0, 'No effect in this slot'),
    "LP2": MultiFXInfo(1, '2 pole lowpass filter'),
    "LP4": MultiFXInfo(2, '4 pole lowpass filter'),
    "HP2": MultiFXInfo(3, '2 pole highpass filter'),
    "HP4": MultiFXInfo(4, '4 pole highpass filter'),
    "BP2": MultiFXInfo(5, '2 pole bandpass filter'),
    "BP4": MultiFXInfo(6, '4 pole bandpass filter'),
    "Notch2": MultiFXInfo(7, '2 pole notch filter'),
    "Notch4": MultiFXInfo(8, '4 pole notch filter'),
    "EQ": MultiFXInfo(9, 'Single band parametric EQ'),
    "Distortion": MultiFXInfo(10, 'Classic hard-clipping distortion effect'),
    "Comb Filter": MultiFXInfo(
        11,
        'Classic comb filter effect to create harsh phasing sound',
    ),
    "Amp/Pan": MultiFXInfo(12, 'Volume and pan knobs'),
    "Limiter": MultiFXInfo(13, 'Classic hard limiter effect'),
    "Saturator": MultiFXInfo(
        14,
        'Classic saturator for soft, warm distortion',
    ),
    "Formant": MultiFXInfo(
        15,
        'A formant filter for creating vocal-like sounds',
    ),
    "Stereo Chorus": MultiFXInfo(
        16,
        'A classic chorus delay effect for creating unison sounds',
    ),
    "Glitch": MultiFXInfo(17, 'A unique distortion effect'),
    "RingMod": MultiFXInfo(18, 'A classic ring modulator effect'),
    "LoFi": MultiFXInfo(
        19,
        'A bit crusher effect for creating retro-style sounds',
    ),
    "S/H": MultiFXInfo(20, 'A classic sample & hold distortion effect'),
    "LP D/W": MultiFXInfo(21, 'A 2 pole lowpass filter with a dry/wet knob'),
    "HP D/W": MultiFXInfo(
        22,
        'A 2 pole highpass filter with a dry/wet knob',
    ),
    "Monofier": MultiFXInfo(23, 'Convert stereo sounds to mono'),
    "LP<-->HP": MultiFXInfo(
        24,
        'Cross fade between highpass and lowpass filters',
    ),
    "Growl Filter": MultiFXInfo(
        25,
        'An aggressive sounding formant filter for creating vocal-like sounds',
    ),
    "LP Screech": MultiFXInfo(
        26,
        'A lowpass filter for classic acid sounds',
    ),
    "Metal Comb": MultiFXInfo(
        27,
        'A comb filter for creating metallic cymbal-like sounds',
    ),
    "Notch D/W": MultiFXInfo(
        28,
        'A 2 pole notch filter with a dry/wet knob',
    ),
    "Foldback": MultiFXInfo(
        29,
        'Foldback distortion for harsh digital sounds',
    ),
    "Notch Spread": MultiFXInfo(
        30,
        'A notch filter with adjustable bandwidth for classic dubstep sounds',
    ),
    "DC Offset": MultiFXInfo(
        31,
        'A DC offset filter for removing very low frequencies',
    ),
    "BP Spread": MultiFXInfo(
        32,
        'A bandpass filter with adjustable bandwidth',
    ),
    "Phaser Static": MultiFXInfo(
        33,
        'A phaser without LFO, modulation using automation',
    ),
    "Flanger Static": MultiFXInfo(
        34,
        'A flanger without LFO, modulation using automation',
    ),
    "Soft Clipper": MultiFXInfo(35, 'Soft clipping distortion'),
    "BP D/W": MultiFXInfo(37, 'A 2 pole bandpass filter with a dry/wet knob'),
    'Ladder4': MultiFXInfo(
        38,
        'A 4 pole ladder lowpass filter.  Be careful with high resonance '
        'values, like a real Moog filter, it will self-oscillate indefinitely'
    ),
}

def mfx_set_tooltip(knobs, idx: int):
    tooltips = MULTIFX_KNOB_TOOLTIPS.get(idx, [])
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

MULTIFX_KNOB_TOOLTIPS = {
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
