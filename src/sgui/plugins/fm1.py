# -*- coding: utf-8 -*-
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

from sglib.math import clip_value
from sgui.widgets import *
from sglib.lib.translate import _
from sglib.log import LOG
from .util import get_screws
import sys

#Total number of LFOs, ADSRs, other envelopes, etc...
#Used for the PolyFX mod matrix
FM1_MODULATOR_COUNT = 4
#How many modular PolyFX
FM1_MODULAR_POLYFX_COUNT = 4
#How many ports per PolyFX, 3 knobs and a combobox
FM1_PORTS_PER_MOD_EFFECT = 4
#How many knobs per PolyFX, 3 knobs
FM1_CONTROLS_PER_MOD_EFFECT = 3
FM1_EFFECTS_GROUPS_COUNT = 1
FM1_OUTPUT0 = 0
FM1_OUTPUT1 = 1
FM1_FIRST_CONTROL_PORT = 2
FM1_ATTACK_MAIN = 2
FM1_DECAY_MAIN = 3
FM1_SUSTAIN_MAIN = 4
FM1_RELEASE_MAIN = 5
FM1_NOISE_AMP = 6
FM1_OSC1_TYPE = 7
FM1_OSC1_PITCH = 8
FM1_OSC1_TUNE = 9
FM1_OSC1_VOLUME = 10
FM1_OSC2_TYPE = 11
FM1_OSC2_PITCH = 12
FM1_OSC2_TUNE = 13
FM1_OSC2_VOLUME = 14
FM1_MAIN_VOLUME = 15
FM1_OSC1_UNISON_VOICES = 16
FM1_OSC1_UNISON_SPREAD = 17
FM1_MAIN_GLIDE = 18
FM1_MAIN_PITCHBEND_AMT = 19
FM1_ATTACK1 = 20
FM1_DECAY1 = 21
FM1_SUSTAIN1 = 22
FM1_RELEASE1 = 23
FM1_ATTACK2 = 24
FM1_DECAY2 = 25
FM1_SUSTAIN2 = 26
FM1_RELEASE2 = 27
FM1_ATTACK_PFX1 = 28
FM1_DECAY_PFX1 = 29
FM1_SUSTAIN_PFX1 = 30
FM1_RELEASE_PFX1 = 31
FM1_ATTACK_PFX2 = 32
FM1_DECAY_PFX2 = 33
FM1_SUSTAIN_PFX2 = 34
FM1_RELEASE_PFX2 = 35
FM1_NOISE_TYPE = 36
FM1_RAMP_ENV_TIME = 37
FM1_LFO_FREQ = 38
FM1_LFO_TYPE = 39
FM1_FX0_KNOB0 = 40
FM1_FX0_KNOB1 = 41
FM1_FX0_KNOB2 = 42
FM1_FX0_COMBOBOX = 43
FM1_FX1_KNOB0 = 44
FM1_FX1_KNOB1 = 45
FM1_FX1_KNOB2 = 46
FM1_FX1_COMBOBOX = 47
FM1_FX2_KNOB0 = 48
FM1_FX2_KNOB1 = 49
FM1_FX2_KNOB2 = 50
FM1_FX2_COMBOBOX = 51
FM1_FX3_KNOB0 = 52
FM1_FX3_KNOB1 = 53
FM1_FX3_KNOB2 = 54
FM1_FX3_COMBOBOX = 55
#PolyFX Mod Matrix
FM1_PFXMATRIX_FIRST_PORT = 56
FM1_PFXMATRIX_GRP0DST0SRC0CTRL0 = 56
FM1_PFXMATRIX_GRP0DST0SRC0CTRL1 = 57
FM1_PFXMATRIX_GRP0DST0SRC0CTRL2 = 58
FM1_PFXMATRIX_GRP0DST0SRC1CTRL0 = 59
FM1_PFXMATRIX_GRP0DST0SRC1CTRL1 = 60
FM1_PFXMATRIX_GRP0DST0SRC1CTRL2 = 61
FM1_PFXMATRIX_GRP0DST0SRC2CTRL0 = 62
FM1_PFXMATRIX_GRP0DST0SRC2CTRL1 = 63
FM1_PFXMATRIX_GRP0DST0SRC2CTRL2 = 64
FM1_PFXMATRIX_GRP0DST0SRC3CTRL0 = 65
FM1_PFXMATRIX_GRP0DST0SRC3CTRL1 = 66
FM1_PFXMATRIX_GRP0DST0SRC3CTRL2 = 67
FM1_PFXMATRIX_GRP0DST1SRC0CTRL0 = 68
FM1_PFXMATRIX_GRP0DST1SRC0CTRL1 = 69
FM1_PFXMATRIX_GRP0DST1SRC0CTRL2 = 70
FM1_PFXMATRIX_GRP0DST1SRC1CTRL0 = 71
FM1_PFXMATRIX_GRP0DST1SRC1CTRL1 = 72
FM1_PFXMATRIX_GRP0DST1SRC1CTRL2 = 73
FM1_PFXMATRIX_GRP0DST1SRC2CTRL0 = 74
FM1_PFXMATRIX_GRP0DST1SRC2CTRL1 = 75
FM1_PFXMATRIX_GRP0DST1SRC2CTRL2 = 76
FM1_PFXMATRIX_GRP0DST1SRC3CTRL0 = 77
FM1_PFXMATRIX_GRP0DST1SRC3CTRL1 = 78
FM1_PFXMATRIX_GRP0DST1SRC3CTRL2 = 79
FM1_PFXMATRIX_GRP0DST2SRC0CTRL0 = 80
FM1_PFXMATRIX_GRP0DST2SRC0CTRL1 = 81
FM1_PFXMATRIX_GRP0DST2SRC0CTRL2 = 82
FM1_PFXMATRIX_GRP0DST2SRC1CTRL0 = 83
FM1_PFXMATRIX_GRP0DST2SRC1CTRL1 = 84
FM1_PFXMATRIX_GRP0DST2SRC1CTRL2 = 85
FM1_PFXMATRIX_GRP0DST2SRC2CTRL0 = 86
FM1_PFXMATRIX_GRP0DST2SRC2CTRL1 = 87
FM1_PFXMATRIX_GRP0DST2SRC2CTRL2 = 88
FM1_PFXMATRIX_GRP0DST2SRC3CTRL0 = 89
FM1_PFXMATRIX_GRP0DST2SRC3CTRL1 = 90
FM1_PFXMATRIX_GRP0DST2SRC3CTRL2 = 91
FM1_PFXMATRIX_GRP0DST3SRC0CTRL0 = 92
FM1_PFXMATRIX_GRP0DST3SRC0CTRL1 = 93
FM1_PFXMATRIX_GRP0DST3SRC0CTRL2 = 94
FM1_PFXMATRIX_GRP0DST3SRC1CTRL0 = 95
FM1_PFXMATRIX_GRP0DST3SRC1CTRL1 = 96
FM1_PFXMATRIX_GRP0DST3SRC1CTRL2 = 97
FM1_PFXMATRIX_GRP0DST3SRC2CTRL0 = 98
FM1_PFXMATRIX_GRP0DST3SRC2CTRL1 = 99
FM1_PFXMATRIX_GRP0DST3SRC2CTRL2 = 100
FM1_PFXMATRIX_GRP0DST3SRC3CTRL0 = 101
FM1_PFXMATRIX_GRP0DST3SRC3CTRL1 = 102
FM1_PFXMATRIX_GRP0DST3SRC3CTRL2 = 103
#End PolyFX Mod Matrix
FM1_ADSR1_CHECKBOX = 105
FM1_ADSR2_CHECKBOX = 106
FM1_LFO_AMP = 107
FM1_LFO_PITCH = 108
FM1_PITCH_ENV_AMT = 109
FM1_OSC2_UNISON_VOICES = 110
FM1_OSC2_UNISON_SPREAD = 111
FM1_LFO_AMOUNT = 112
FM1_OSC3_TYPE = 113
FM1_OSC3_PITCH = 114
FM1_OSC3_TUNE = 115
FM1_OSC3_VOLUME = 116
FM1_OSC3_UNISON_VOICES = 117
FM1_OSC3_UNISON_SPREAD = 118
FM1_OSC1_FM1 = 119
FM1_OSC1_FM2 = 120
FM1_OSC1_FM3 = 121
FM1_OSC2_FM1 = 122
FM1_OSC2_FM2 = 123
FM1_OSC2_FM3 = 124
FM1_OSC3_FM1 = 125
FM1_OSC3_FM2 = 126
FM1_OSC3_FM3 = 127
FM1_ATTACK3 = 128
FM1_DECAY3 = 129
FM1_SUSTAIN3 = 130
FM1_RELEASE3 = 131
FM1_ADSR3_CHECKBOX = 132

FM1_PFXMATRIX_GRP0DST0SRC4CTRL0 = 133
FM1_PFXMATRIX_GRP0DST0SRC4CTRL1 = 134
FM1_PFXMATRIX_GRP0DST0SRC4CTRL2 = 135
FM1_PFXMATRIX_GRP0DST1SRC4CTRL0 = 136
FM1_PFXMATRIX_GRP0DST1SRC4CTRL1 = 137
FM1_PFXMATRIX_GRP0DST1SRC4CTRL2 = 138
FM1_PFXMATRIX_GRP0DST2SRC4CTRL0 = 139
FM1_PFXMATRIX_GRP0DST2SRC4CTRL1 = 140
FM1_PFXMATRIX_GRP0DST2SRC4CTRL2 = 141
FM1_PFXMATRIX_GRP0DST3SRC4CTRL0 = 142
FM1_PFXMATRIX_GRP0DST3SRC4CTRL1 = 143
FM1_PFXMATRIX_GRP0DST3SRC4CTRL2 = 144

FM1_PFXMATRIX_GRP0DST0SRC5CTRL0 = 145
FM1_PFXMATRIX_GRP0DST0SRC5CTRL1 = 146
FM1_PFXMATRIX_GRP0DST0SRC5CTRL2 = 147
FM1_PFXMATRIX_GRP0DST1SRC5CTRL0 = 148
FM1_PFXMATRIX_GRP0DST1SRC5CTRL1 = 149
FM1_PFXMATRIX_GRP0DST1SRC5CTRL2 = 150
FM1_PFXMATRIX_GRP0DST2SRC5CTRL0 = 151
FM1_PFXMATRIX_GRP0DST2SRC5CTRL1 = 152
FM1_PFXMATRIX_GRP0DST2SRC5CTRL2 = 153
FM1_PFXMATRIX_GRP0DST3SRC5CTRL0 = 154
FM1_PFXMATRIX_GRP0DST3SRC5CTRL1 = 155
FM1_PFXMATRIX_GRP0DST3SRC5CTRL2 = 156
FM1_PERC_ENV_TIME1 = 157
FM1_PERC_ENV_PITCH1 = 158
FM1_PERC_ENV_TIME2 = 159
FM1_PERC_ENV_PITCH2 = 160
FM1_PERC_ENV_ON = 161
FM1_RAMP_CURVE = 162
FM1_MONO_MODE = 163

FM1_OSC4_TYPE = 164
FM1_OSC4_PITCH = 165
FM1_OSC4_TUNE = 166
FM1_OSC4_VOLUME = 167
FM1_OSC4_UNISON_VOICES = 168
FM1_OSC4_UNISON_SPREAD = 169
FM1_OSC1_FM4 = 170
FM1_OSC2_FM4 = 171
FM1_OSC3_FM4 = 172
FM1_OSC4_FM1 = 173
FM1_OSC4_FM2 = 174
FM1_OSC4_FM3 = 175
FM1_OSC4_FM4 = 176
FM1_ATTACK4 = 177
FM1_DECAY4 =  178
FM1_SUSTAIN4 = 179
FM1_RELEASE4 = 180
FM1_ADSR4_CHECKBOX = 181

FM1_FM_MACRO1 = 182
FM1_FM_MACRO1_OSC1_FM1 = 183
FM1_FM_MACRO1_OSC1_FM2 = 184
FM1_FM_MACRO1_OSC1_FM3 = 185
FM1_FM_MACRO1_OSC1_FM4 = 186
FM1_FM_MACRO1_OSC2_FM1 = 187
FM1_FM_MACRO1_OSC2_FM2 = 188
FM1_FM_MACRO1_OSC2_FM3 = 189
FM1_FM_MACRO1_OSC2_FM4 = 190
FM1_FM_MACRO1_OSC3_FM1 = 191
FM1_FM_MACRO1_OSC3_FM2 = 192
FM1_FM_MACRO1_OSC3_FM3 = 193
FM1_FM_MACRO1_OSC3_FM4 = 194
FM1_FM_MACRO1_OSC4_FM1 = 195
FM1_FM_MACRO1_OSC4_FM2 = 196
FM1_FM_MACRO1_OSC4_FM3 = 197
FM1_FM_MACRO1_OSC4_FM4 = 198

FM1_FM_MACRO2 = 199
FM1_FM_MACRO2_OSC1_FM1 = 200
FM1_FM_MACRO2_OSC1_FM2 = 201
FM1_FM_MACRO2_OSC1_FM3 = 202
FM1_FM_MACRO2_OSC1_FM4 = 203
FM1_FM_MACRO2_OSC2_FM1 = 204
FM1_FM_MACRO2_OSC2_FM2 = 205
FM1_FM_MACRO2_OSC2_FM3 = 206
FM1_FM_MACRO2_OSC2_FM4 = 207
FM1_FM_MACRO2_OSC3_FM1 = 208
FM1_FM_MACRO2_OSC3_FM2 = 209
FM1_FM_MACRO2_OSC3_FM3 = 210
FM1_FM_MACRO2_OSC3_FM4 = 211
FM1_FM_MACRO2_OSC4_FM1 = 212
FM1_FM_MACRO2_OSC4_FM2 = 213
FM1_FM_MACRO2_OSC4_FM3 = 214
FM1_FM_MACRO2_OSC4_FM4 = 215

FM1_LFO_PHASE = 216

FM1_FM_MACRO1_OSC1_VOL = 217
FM1_FM_MACRO1_OSC2_VOL = 218
FM1_FM_MACRO1_OSC3_VOL = 219
FM1_FM_MACRO1_OSC4_VOL = 220

FM1_FM_MACRO2_OSC1_VOL = 221
FM1_FM_MACRO2_OSC2_VOL = 222
FM1_FM_MACRO2_OSC3_VOL = 223
FM1_FM_MACRO2_OSC4_VOL = 224
FM1_LFO_PITCH_FINE = 225
FM1_ADSR_PREFX = 226

FM1_ADSR1_DELAY = 227
FM1_ADSR2_DELAY = 228
FM1_ADSR3_DELAY = 229
FM1_ADSR4_DELAY = 230

FM1_ADSR1_HOLD = 231
FM1_ADSR2_HOLD = 232
FM1_ADSR3_HOLD = 233
FM1_ADSR4_HOLD = 234

FM1_PFX_ADSR_DELAY = 235
FM1_PFX_ADSR_F_DELAY = 236
FM1_PFX_ADSR_HOLD = 237
FM1_PFX_ADSR_F_HOLD = 238
FM1_HOLD_MAIN  = 239

FM1_DELAY_NOISE = 240
FM1_ATTACK_NOISE = 241
FM1_HOLD_NOISE = 242
FM1_DECAY_NOISE = 243
FM1_SUSTAIN_NOISE = 244
FM1_RELEASE_NOISE = 245
FM1_ADSR_NOISE_ON = 246

FM1_DELAY_LFO = 247
FM1_ATTACK_LFO = 248
FM1_HOLD_LFO = 249
FM1_DECAY_LFO = 250
FM1_SUSTAIN_LFO = 251
FM1_RELEASE_LFO = 252
FM1_ADSR_LFO_ON = 253


FM1_OSC5_TYPE = 254
FM1_OSC5_PITCH = 255
FM1_OSC5_TUNE = 256
FM1_OSC5_VOLUME = 257
FM1_OSC5_UNISON_VOICES = 258
FM1_OSC5_UNISON_SPREAD = 259
FM1_OSC1_FM5 = 260
FM1_OSC2_FM5 = 261
FM1_OSC3_FM5 = 262
FM1_OSC4_FM5 = 263
FM1_OSC5_FM5 = 264
FM1_OSC6_FM5 = 265
FM1_ADSR5_DELAY = 266
FM1_ATTACK5 = 267
FM1_ADSR5_HOLD = 268
FM1_DECAY5 = 269
FM1_SUSTAIN5 = 270
FM1_RELEASE5 = 271
FM1_ADSR5_CHECKBOX = 272

FM1_OSC6_TYPE = 273
FM1_OSC6_PITCH = 274
FM1_OSC6_TUNE = 275
FM1_OSC6_VOLUME = 276
FM1_OSC6_UNISON_VOICES = 277
FM1_OSC6_UNISON_SPREAD = 278
FM1_OSC1_FM6 = 279
FM1_OSC2_FM6 = 280
FM1_OSC3_FM6 = 281
FM1_OSC4_FM6 = 282
FM1_OSC5_FM6 = 283
FM1_OSC6_FM6 = 284
FM1_ADSR6_DELAY = 285
FM1_ATTACK6 = 286
FM1_ADSR6_HOLD = 287
FM1_DECAY6 = 288
FM1_SUSTAIN6 = 289
FM1_RELEASE6 = 290
FM1_ADSR6_CHECKBOX = 291


FM1_FM_MACRO1_OSC1_FM5 = 292
FM1_FM_MACRO1_OSC2_FM5 = 293
FM1_FM_MACRO1_OSC3_FM5 = 294
FM1_FM_MACRO1_OSC4_FM5 = 295
FM1_FM_MACRO1_OSC5_FM5 = 296
FM1_FM_MACRO1_OSC6_FM5 = 297

FM1_FM_MACRO1_OSC1_FM6 = 298
FM1_FM_MACRO1_OSC2_FM6 = 299
FM1_FM_MACRO1_OSC3_FM6 = 300
FM1_FM_MACRO1_OSC4_FM6 = 301
FM1_FM_MACRO1_OSC5_FM6 = 302
FM1_FM_MACRO1_OSC6_FM6 = 303

FM1_FM_MACRO1_OSC5_FM1 = 304
FM1_FM_MACRO1_OSC5_FM2 = 305
FM1_FM_MACRO1_OSC5_FM3 = 306
FM1_FM_MACRO1_OSC5_FM4 = 307

FM1_FM_MACRO1_OSC6_FM1 = 308
FM1_FM_MACRO1_OSC6_FM2 = 309
FM1_FM_MACRO1_OSC6_FM3 = 310
FM1_FM_MACRO1_OSC6_FM4 = 311

FM1_FM_MACRO1_OSC5_VOL = 312
FM1_FM_MACRO1_OSC6_VOL = 313

FM1_FM_MACRO2_OSC1_FM5 = 314
FM1_FM_MACRO2_OSC2_FM5 = 315
FM1_FM_MACRO2_OSC3_FM5 = 316
FM1_FM_MACRO2_OSC4_FM5 = 317
FM1_FM_MACRO2_OSC5_FM5 = 318
FM1_FM_MACRO2_OSC6_FM5 = 319

FM1_FM_MACRO2_OSC1_FM6 = 320
FM1_FM_MACRO2_OSC2_FM6 = 321
FM1_FM_MACRO2_OSC3_FM6 = 322
FM1_FM_MACRO2_OSC4_FM6 = 323
FM1_FM_MACRO2_OSC5_FM6 = 324
FM1_FM_MACRO2_OSC6_FM6 = 325

FM1_FM_MACRO2_OSC5_FM1 = 326
FM1_FM_MACRO2_OSC5_FM2 = 327
FM1_FM_MACRO2_OSC5_FM3 = 328
FM1_FM_MACRO2_OSC5_FM4 = 329

FM1_FM_MACRO2_OSC6_FM1 = 330
FM1_FM_MACRO2_OSC6_FM2 = 331
FM1_FM_MACRO2_OSC6_FM3 = 332
FM1_FM_MACRO2_OSC6_FM4 = 333

FM1_FM_MACRO2_OSC5_VOL = 334
FM1_FM_MACRO2_OSC6_VOL = 335

FM1_OSC5_FM1 = 336
FM1_OSC5_FM2 = 337
FM1_OSC5_FM3 = 338
FM1_OSC5_FM4 = 339

FM1_OSC6_FM1 = 340
FM1_OSC6_FM2 = 341
FM1_OSC6_FM3 = 342
FM1_OSC6_FM4 = 343
FM1_NOISE_PREFX = 344

FM1_PFXMATRIX_GRP0DST0SRC6CTRL0 = 345
FM1_PFXMATRIX_GRP0DST0SRC6CTRL1 = 346
FM1_PFXMATRIX_GRP0DST0SRC6CTRL2 = 347
FM1_PFXMATRIX_GRP0DST1SRC6CTRL0 = 348
FM1_PFXMATRIX_GRP0DST1SRC6CTRL1 = 349
FM1_PFXMATRIX_GRP0DST1SRC6CTRL2 = 350
FM1_PFXMATRIX_GRP0DST2SRC6CTRL0 = 351
FM1_PFXMATRIX_GRP0DST2SRC6CTRL1 = 352
FM1_PFXMATRIX_GRP0DST2SRC6CTRL2 = 353
FM1_PFXMATRIX_GRP0DST3SRC6CTRL0 = 354
FM1_PFXMATRIX_GRP0DST3SRC6CTRL1 = 355
FM1_PFXMATRIX_GRP0DST3SRC6CTRL2 = 356

FM1_PFXMATRIX_GRP0DST0SRC7CTRL0 = 357
FM1_PFXMATRIX_GRP0DST0SRC7CTRL1 = 358
FM1_PFXMATRIX_GRP0DST0SRC7CTRL2 = 359
FM1_PFXMATRIX_GRP0DST1SRC7CTRL0 = 360
FM1_PFXMATRIX_GRP0DST1SRC7CTRL1 = 361
FM1_PFXMATRIX_GRP0DST1SRC7CTRL2 = 362
FM1_PFXMATRIX_GRP0DST2SRC7CTRL0 = 363
FM1_PFXMATRIX_GRP0DST2SRC7CTRL1 = 364
FM1_PFXMATRIX_GRP0DST2SRC7CTRL2 = 365
FM1_PFXMATRIX_GRP0DST3SRC7CTRL0 = 366
FM1_PFXMATRIX_GRP0DST3SRC7CTRL1 = 367
FM1_PFXMATRIX_GRP0DST3SRC7CTRL2 = 368

FM1_MIN_NOTE = 369
FM1_MAX_NOTE = 370
FM1_MAIN_PITCH = 371

FM1_ADSR_LIN_MAIN = 372
FM1_MAIN_PAN = 373
FM1_OSC1_PAN = 374
FM1_OSC2_PAN = 375
FM1_OSC3_PAN = 376
FM1_OSC4_PAN = 377
FM1_OSC5_PAN = 378
FM1_OSC6_PAN = 379

FM1_ATTACK_MAIN_START = 380
FM1_ATTACK_MAIN_END = 381
FM1_DECAY_MAIN_START = 382
FM1_DECAY_MAIN_END = 383
FM1_SUSTAIN_MAIN_START = 384
FM1_SUSTAIN_MAIN_END = 385
FM1_RELEASE_MAIN_START = 386
FM1_RELEASE_MAIN_END = 387

OSC_TYPE_LOOKUP = {
    "Off": (0, 'Disable this oscillator'),
    "Plain Saw": (1, 'Classic analog style saw wave'),
    "SuperbSaw": (2, 'Modelled after a legendary pad synthesizer'),
    "Viral Saw": (3, 'Modelled after a legendary bass and lead synthesizer'),
    "Soft Saw": (4, 'A saw wave with less high frequencies'),
    "Mid Saw": (5, 'A saw wave with emphasized mid-range frequencies'),
    "Lush Saw": (6, 'A complex, nuanced saw wave, tuned for unison voices'),
    "Evil Square": (7, 'An aggressive square wave sound'),
    "Punchy Square": (8, 'A square wave that really cuts through the mix'),
    "Soft Square": (9, 'A square wave suitable for progressive sounds'),
    "Pink Glitch": (10, 'A repeating pink noise glitch'),
    "White Glitch": (11, 'A repeating white noise glitch'),
    "Acid": (12, 'A harsh, distorted lead sound'),
    "Screetch": (13, 'An aggressive, harsh lead sound'),
    "Thick Bass": (14, 'Lush sub-bass oscillator'),
    "Rattler": (15, 'A deep sub-bass oscillator'),
    "Deep Saw": (16, 'A very soft saw wave suitable for sub-bass'),
    "Sine": (17, 'A classic sine wave for sub-bass or DX7 style FM synthesis'),
    "(Additive 1)": (
        18,
        'Custom additive oscillator, see the Additive tab',
    ),
    "(Additive 2)": (
        19,
        'Custom additive oscillator, see the Additive tab',
    ),
    "(Additive 3)": (
        20,
        'Custom additive oscillator, see the Additive tab',
    ),
}
OSC_TYPES = [
    "Off",
    ("Saw", [
        "Plain Saw",
        "SuperbSaw",
        "Viral Saw",
        "Soft Saw",
        "Mid Saw",
        "Lush Saw",
    ]),
    ("Square", [
        "Evil Square",
        "Punchy Square",
        "Soft Square",
    ]),
    ("Glitch", [
        "Pink Glitch",
        "White Glitch",
        "Acid",
        "Screetch",
    ]),
    ("Sine", [
        "Thick Bass",
        "Rattler",
        "Deep Saw",
        "Sine",
    ]),
    ("Custom", [
        "(Additive 1)",
        "(Additive 2)",
        "(Additive 3)",
    ]),
]

FM1_PORT_MAP = {
    "Main Attack": FM1_ATTACK_MAIN,
    "Main Hold": FM1_HOLD_MAIN,
    "Main Decay": FM1_DECAY_MAIN,
    "Main Sustain": FM1_SUSTAIN_MAIN,
    "Main Release": FM1_RELEASE_MAIN,
    "Noise Amp": FM1_OSC1_TYPE,
    "Main Glide": 18,
    "Osc1 Attack": FM1_ATTACK1,
    "Osc1 Decay": FM1_DECAY1,
    "Osc1 Sustain": FM1_SUSTAIN1,
    "Osc1 Release": FM1_RELEASE1,
    "Osc2 Attack": FM1_ATTACK2,
    "Osc2 Decay": FM1_DECAY2,
    "Osc2 Sustain": FM1_SUSTAIN2,
    "Osc2 Release": FM1_RELEASE2,
    "Pan": FM1_MAIN_PAN,
    "PFX ADSR1 Attack": 28,
    "PFX ADSR1 Decay": 29,
    "PFX ADSR1 Sustain": "30",
    "PFX ADSR1 Release": "31",
    "PFX ADSR2 Attack": "32",
    "PFX ADSR2 Decay": "33",
    "PFX ADSR2 Sustain": "34",
    "PFX ADSR2 Release": "35",
    "Pitch Env Time": "37",
    "LFO Freq": "38",
    "FX0 Knob0": "40",
    "FX0 Knob1": "41",
    "FX0 Knob2": "42",
    "FX1 Knob0": "44",
    "FX1 Knob1": "45",
    "FX1 Knob2": "46",
    "FX2 Knob0": "48",
    "FX2 Knob1": "49",
    "FX2 Knob2": "50",
    "FX3 Knob0": "52",
    "FX3 Knob1": "53",
    "FX3 Knob2": "54",
    "LFO Amp": "107",
    "LFO Pitch": "108",
    "LFO Pitch Fine": FM1_LFO_PITCH_FINE,
    "Pitch Env Amt": "109",
    "LFO Amount": "112",
    "Osc1 FM1": FM1_OSC1_FM1,
    "Osc1 FM2": FM1_OSC1_FM2,
    "Osc1 FM3": FM1_OSC1_FM3,
    "Osc1 FM4": FM1_OSC1_FM4,
    "Osc1 FM5": FM1_OSC1_FM5,
    "Osc1 FM6": FM1_OSC1_FM6,
    "Osc2 FM1": FM1_OSC2_FM1,
    "Osc2 FM2": FM1_OSC2_FM2,
    "Osc2 FM3": FM1_OSC2_FM3,
    "Osc2 FM4": FM1_OSC2_FM4,
    "Osc2 FM5": FM1_OSC2_FM5,
    "Osc2 FM6": FM1_OSC2_FM6,
    "Osc3 FM1": FM1_OSC3_FM1,
    "Osc3 FM2": FM1_OSC3_FM2,
    "Osc3 FM3": FM1_OSC3_FM3,
    "Osc3 FM4": FM1_OSC3_FM4,
    "Osc3 FM5": FM1_OSC3_FM5,
    "Osc3 FM6": FM1_OSC3_FM6,
    "Osc4 FM1": FM1_OSC4_FM1,
    "Osc4 FM2": FM1_OSC4_FM2,
    "Osc4 FM3": FM1_OSC4_FM3,
    "Osc4 FM4": FM1_OSC4_FM4,
    "Osc4 FM5": FM1_OSC4_FM5,
    "Osc4 FM6": FM1_OSC4_FM6,
    "Osc5 FM1": FM1_OSC5_FM1,
    "Osc5 FM2": FM1_OSC5_FM2,
    "Osc5 FM3": FM1_OSC5_FM3,
    "Osc5 FM4": FM1_OSC5_FM4,
    "Osc5 FM5": FM1_OSC5_FM5,
    "Osc5 FM6": FM1_OSC5_FM6,
    "Osc6 FM1": FM1_OSC6_FM1,
    "Osc6 FM2": FM1_OSC6_FM2,
    "Osc6 FM3": FM1_OSC6_FM3,
    "Osc6 FM4": FM1_OSC6_FM4,
    "Osc6 FM5": FM1_OSC6_FM5,
    "Osc6 FM6": FM1_OSC6_FM6,
    "Osc3 Attack": FM1_ATTACK3,
    "Osc3 Decay": FM1_DECAY3,
    "Osc3 Sustain": FM1_SUSTAIN3,
    "Osc3 Release": FM1_RELEASE3,
    "FM Macro 1": FM1_FM_MACRO1,
    "FM Macro 2": FM1_FM_MACRO2,
    "Osc4 Attack": FM1_ATTACK4,
    "Osc4 Decay": FM1_DECAY4,
    "Osc4 Sustain": FM1_SUSTAIN4,
    "Osc4 Release": FM1_RELEASE4,
    "Osc5 Attack": FM1_ATTACK5,
    "Osc5 Decay": FM1_DECAY5,
    "Osc5 Sustain": FM1_SUSTAIN5,
    "Osc5 Release": FM1_RELEASE5,
    "Osc6 Attack": FM1_ATTACK6,
    "Osc6 Decay": FM1_DECAY6,
    "Osc6 Sustain": FM1_SUSTAIN6,
    "Osc6 Release": FM1_RELEASE6,
    "Osc1 Delay": FM1_ADSR1_DELAY,
    "Osc2 Delay": FM1_ADSR2_DELAY,
    "Osc3 Delay": FM1_ADSR3_DELAY,
    "Osc4 Delay": FM1_ADSR4_DELAY,
    "Osc5 Delay": FM1_ADSR5_DELAY,
    "Osc6 Delay": FM1_ADSR6_DELAY,
    "Osc1 Hold": FM1_ADSR1_HOLD,
    "Osc2 Hold": FM1_ADSR2_HOLD,
    "Osc3 Hold": FM1_ADSR3_HOLD,
    "Osc4 Hold": FM1_ADSR4_HOLD,
    "Osc5 Hold": FM1_ADSR5_HOLD,
    "Osc6 Hold": FM1_ADSR6_HOLD,
}

STYLESHEET = """\
QWidget,
QMenu,
QMenu::item {
    background-color: #aaaaaa;
	color: #222222;
}

QMenu::separator
{
    height: 2px;
    background-color: #222222;
}

QWidget:item:hover,
QWidget:item:selected
{
    background-color: #222222;
    color: #cccccc;
}

QLabel {
    border: 1px solid #222222;
}

QLabel#transparent {
    background: none;
    border: none;
    color: #222222;
}

QComboBox#plugin_name_label {
    background: transparent;
    border: transparent;
    color: #222222;
}

QGroupBox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #aaaaaa, stop: 0.5 #9c9c9c, stop: 1 #aaaaaa
    );
    border: 2px solid #222222;
    color: #222222;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* position at the top center */
    padding: 0 3px;
    background-color: #aaaaaa;
    border: 2px solid #222222;
}

QHeaderView::section {
    background-color: #aaaaaa;
	color: #222222;
    border: 1px solid #222222;
    padding: 4px;
}

QLineEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #6a6a6a, stop: 0.5 #828282, stop: 1 #6a6a6a
    );
    border: 1px solid #222222;
    border-radius: 6px;
    color: #222222;
}

QTabBar::tab
{
    background-color: #aaaaaa;
    border-bottom-style: none;
    border: 1px solid #222222;
    color: #222222;
    margin-right: -1px;
    padding-bottom: 2px;
    padding-left: 10px;
    padding-right: 10px;
    padding-top: 3px;
}


QTabWidget::tab-bar
{
    left: 5px;
}

QTabWidget::pane
{
    /*border: 1px solid #444;*/
    border-top: 2px solid #cccccc;
    top: 1px;
}

QTabBar::tab:last
{
    /* the last selected tab has nothing to overlap with on the right */
    margin-right: 0;
}

QTabBar::tab:first:!selected
{
    /* the last selected tab has nothing to overlap with on the right */
    margin-left: 0px;
}

QTabBar::tab:!selected
{
    background-color: #aaaaaa;
    border-bottom-style: solid;
    color: #222222;
}

QTabBar::tab:!selected:hover,
QTabBar::tab:selected
{
    background-color: #222222;
    color: #cccccc;
    margin-bottom: 0px;
}

QScrollBar:horizontal
{
    background: #aaaaaa;
    border: 1px solid #222222;
    height: 15px;
    margin: 0px 16px 0 16px;
}

QScrollBar::add-line:horizontal,
QScrollBar::handle:horizontal,
QScrollBar::sub-line:horizontal
{
    background: #aaaaaa;
}

QScrollBar::add-line:vertical,
QScrollBar::handle:vertical,
QScrollBar::sub-line:vertical
{
    background: #aaaaaa;
}

QScrollBar::add-line:horizontal,
QScrollBar::add-line:vertical,
QScrollBar::handle:horizontal,
QScrollBar::handle:vertical,
QScrollBar::sub-line:horizontal,
QScrollBar::sub-line:vertical
{
    min-height: 20px;
}

QScrollBar::add-line:horizontal
{
    border: 1px solid #222222;
    subcontrol-origin: margin;
    subcontrol-position: right;
    width: 14px;
}

QScrollBar::sub-line:horizontal
{
    border: 1px solid #222222;
    subcontrol-origin: margin;
    subcontrol-position: left;
    width: 14px;
}

QScrollBar[hide="true"]::down-arrow:vertical,
QScrollBar[hide="true"]::left-arrow:horizontal,
QScrollBar[hide="true"]::right-arrow:horizontal,
QScrollBar[hide="true"]::up-arrow:vertical
{
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal
{
    background: #222222;
    border: 1px solid #222222;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical
{
    background: #222222;
    border: 1px solid #222222;
}

QScrollBar:vertical
{
    background: #666666;
    border: 1px solid #222222;
    margin: 16px 0 16px 0;
    width: 15px;
}

QScrollBar::handle:vertical
{
    min-height: 20px;
}

QScrollBar::add-line:vertical
{
    border: 1px solid #222222;
    height: 14px;
    subcontrol-origin: margin;
    subcontrol-position: bottom;
}

QScrollBar::sub-line:vertical
{
    border: 1px solid #222222;
    height: 14px;
    subcontrol-origin: margin;
    subcontrol-position: top;
}

QAbstractItemView
{
    background-color: #aaaaaa;
    border: 2px solid #222222;
    selection-background-color: #cccccc;
}

QComboBox::drop-down
{
    border-bottom-right-radius: 3px;
    border-left-color: #222222;
    border-left-style: solid; /* just a single line */
    border-left-width: 0px;
    border-top-right-radius: 3px; /* same radius as the QComboBox */
    color: #cccccc;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
}

QComboBox::down-arrow
{
    image: url({{ PLUGIN_ASSETS_DIR }}/drop-down.svg);
}

QCheckBox,
QRadioButton
{
    background-color: none;
    margin: 3px;
    padding: 0px;
}

QCheckBox::indicator,
QRadioButton::indicator
{
    background-color: #aaaaaa;
    border-radius: 6px;
    border: 1px solid #222222;
    color: #cccccc;
    height: 18px;
    margin-left: 6px;
    width: 18px;
}

QCheckBox::indicator:checked,
QRadioButton::indicator:checked
{
    background-color: qradialgradient(
        cx: 0.5, cy: 0.5,
        fx: 0.5, fy: 0.5,
        radius: 1.0,
        stop: 0.25 #222222,
        stop: 0.3 #aaaaaa
    );
}

QRadioButton::indicator:hover,
QCheckBox::indicator:hover
{
    border: 1px solid #ffffff;
}

QWidget#left_logo {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #4b372a, stop: 1 #463123
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/fm1/logo-left.svg);
    background-position: center;
    background-repeat: no-repeat;
    border: none;
}

QWidget#right_logo {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #4b372a, stop: 1 #463123
    );
    background-image: url({{ PLUGIN_ASSETS_DIR }}/logo-right.svg);
    background-position: center;
    background-repeat: no-repeat;
    border: none;
}

QWidget::item:hover,
QWidget::item:selected,
QMenu::item:hover,
QMenu::item:selected
{
    background-color: #222222;
    color: #aaaaaa;
}

QWidget::item,
QMenu::item
{
    background-color: #aaaaaa;
    color: #222222;
}

QMenu::separator
{
    height: 2px;
    background-color: #222222;
}

QMenu,
QMenu::item,
QWidget#plugin_window {
    background: #aaaaaa;
    color: #222222;
}
"""


class fm1_plugin_ui(AbstractPluginUI):
    def __init__(self, *args, **kwargs):
        AbstractPluginUI.__init__(
            self,
            *args,
            stylesheet=STYLESHEET,
            **kwargs,
        )
        self._plugin_name = "FM1"
        self.is_instrument = True

        knob_kwargs = {
            'arc_brush': QColor('#222222'),
            'arc_bg_brush': QColor("#5a5a5a"),
            'arc_width_pct': 12.0,
            'draw_line': True,
            'fg_svg': None,
        }

        self.fm_knobs = []
        self.fm_origin = None
        self.fm_macro_spinboxes = [[] for x in range(2)]

        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]

        self.tab_widget = QTabWidget()
        self.main_hlayout = QHBoxLayout()
        left_screws = get_screws()
        left_logo = QWidget()
        left_logo.setObjectName("left_logo")
        left_logo.setLayout(left_screws)
        self.main_hlayout.addWidget(left_logo)
        self.main_hlayout.addWidget(self.tab_widget)
        right_screws = get_screws()
        right_logo = QWidget()
        right_logo.setObjectName("right_logo")
        right_logo.setLayout(right_screws)
        self.main_hlayout.addWidget(right_logo)
        self.layout.addLayout(self.main_hlayout)

        self.osc_tab = QWidget()
        self.osc_tab_vlayout = QVBoxLayout(self.osc_tab)
        self.osc_scrollarea = QScrollArea()
        self.osc_scrollarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.osc_scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
        )
        self.tab_widget.addTab(self.osc_tab, _("Oscillators"))
        self.fm_tab = QWidget()
        self.tab_widget.addTab(self.fm_tab, _("FM"))
        self.modulation_tab = QWidget()
        self.tab_widget.addTab(self.modulation_tab, _("Modulation"))
        self.poly_fx_tab = QWidget()
        self.tab_widget.addTab(self.poly_fx_tab, _("PolyFX"))
        self.osc_tab_widget = QWidget()
        self.osc_tab_widget.setObjectName("plugin_ui")
        self.osc_scrollarea.setWidget(self.osc_tab_widget)
        self.osc_scrollarea.setWidgetResizable(True)
        self.oscillator_layout = QVBoxLayout(self.osc_tab_widget)
        self.preset_manager = preset_manager_widget(
            self.get_plugin_name(), self.configure_dict,
            self.reconfigure_plugin)
        self.preset_hlayout = QHBoxLayout()
        self.preset_hlayout.addWidget(self.preset_manager.group_box)
        self.preset_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        self.osc_tab_vlayout.addLayout(self.preset_hlayout)
        self.osc_tab_vlayout.addWidget(self.osc_scrollarea)

        self.hlayout0 = QHBoxLayout()
        self.oscillator_layout.addLayout(self.hlayout0)
        self.hlayout0.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        f_knob_size = 39

        for f_i in range(1, 7):
            f_hlayout1 = QHBoxLayout()
            self.oscillator_layout.addLayout(f_hlayout1)
            f_osc1 = osc_widget(
                f_knob_size,
                getattr(sys.modules[__name__], "FM1_OSC{}_PITCH".format(f_i)),
                getattr(sys.modules[__name__], "FM1_OSC{}_TUNE".format(f_i)),
                getattr(
                    sys.modules[__name__],
                    "FM1_OSC{}_VOLUME".format(f_i)
                ),
                getattr(sys.modules[__name__], "FM1_OSC{}_TYPE".format(f_i)),
                OSC_TYPES,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                _("Oscillator {}".format(f_i)),
                self.port_dict,
                self.preset_manager,
                1 if f_i == 1 else 0,
                knob_kwargs=knob_kwargs,
                nested_lookup=OSC_TYPE_LOOKUP,
                vol_min_text="-inf",
            )
            f_osc1.pitch_knob.control.setRange(-72, 72)
            f_osc1_uni_voices = knob_control(
                f_knob_size, _("Unison"),
                getattr(
                    sys.modules[__name__],
                    "FM1_OSC{}_UNISON_VOICES".format(f_i)
                ),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                1,
                7,
                1,
                KC_INTEGER,
                self.port_dict,
                self.preset_manager,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    "The number of unison voices for this oscillator.  "
                    "lower values have a thinner sound and work better "
                    "with FM synthesis, higher values have a thicker sound"
                )
            )
            f_osc1_uni_voices.add_to_grid_layout(f_osc1.grid_layout, 4)
            f_osc1_uni_spread = knob_control(
                f_knob_size,
                _("Spread"),
                getattr(
                    sys.modules[__name__],
                    "FM1_OSC{}_UNISON_SPREAD".format(f_i),
                ),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                0,
                100,
                50,
                KC_DECIMAL,
                self.port_dict,
                self.preset_manager,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    'Unison spread, in semitones.  How much to detune\n'
                    'oscillators when unison is more than 1'
                )
            )
            f_osc1_uni_spread.add_to_grid_layout(f_osc1.grid_layout, 5)

            knob_kwargs['arc_type'] = ArcType.BIDIRECTIONAL
            osc_pan = knob_control(
                f_knob_size,
                _("Pan"),
                getattr(
                    sys.modules[__name__],
                    f"FM1_OSC{f_i}_PAN",
                ),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                -100,
                100,
                0,
                KC_DECIMAL,
                self.port_dict,
                self.preset_manager,
                knob_kwargs=knob_kwargs,
                tooltip=(
                    'Oscillator pan.  Pan individual oscillators between\n'
                    'the left and right channels'
                ),
            )
            knob_kwargs.pop('arc_type')
            osc_pan.add_to_grid_layout(f_osc1.grid_layout, 6)

            f_hlayout1.addWidget(f_osc1.group_box)

            f_adsr_amp1 = adsr_widget(
                f_knob_size,
                True,
                getattr(sys.modules[__name__], "FM1_ATTACK{}".format(f_i)),
                getattr(sys.modules[__name__], "FM1_DECAY{}".format(f_i)),
                getattr(sys.modules[__name__], "FM1_SUSTAIN{}".format(f_i)),
                getattr(sys.modules[__name__], "FM1_RELEASE{}".format(f_i)),
                _("DAHDSR Osc{}".format(f_i)),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict, self.preset_manager,
                a_knob_type=KC_LOG_TIME,
                a_delay_port=getattr(
                    sys.modules[__name__],
                    "FM1_ADSR{}_DELAY".format(f_i)
                ),
                a_hold_port=getattr(
                    sys.modules[__name__],
                    "FM1_ADSR{}_HOLD".format(f_i)
                ),
                knob_kwargs=knob_kwargs,
            )
            f_hlayout1.addWidget(f_adsr_amp1.groupbox)

            f_adsr_amp1_checkbox = checkbox_control(
                _("On"),
                getattr(sys.modules[__name__],
                "FM1_ADSR{}_CHECKBOX".format(f_i)),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict,
                self.preset_manager,
                tooltip='Enable the ADSR envelope for this oscillator',
            )
            f_adsr_amp1_checkbox.add_to_grid_layout(f_adsr_amp1.layout, 15)


        # FM Matrix

        self.fm_gridlayout = QGridLayout(self.fm_tab)
        self.fm_gridlayout.addWidget(QLabel("FM Matrix"), 0, 0)
        self.fm_matrix = QTableWidget()

        self.fm_matrix.setCornerButtonEnabled(False)
        self.fm_matrix.setRowCount(6)
        self.fm_matrix.setColumnCount(6)
        self.fm_matrix.setFixedHeight(240)
        f_fm_src_matrix_labels = ["From Osc{}".format(x) for x in range(1, 7)]
        f_fm_dest_matrix_labels = ["To\nOsc{}".format(x) for x in range(1, 7)]
        self.fm_matrix.setHorizontalHeaderLabels(f_fm_dest_matrix_labels)
        self.fm_matrix.setVerticalHeaderLabels(f_fm_src_matrix_labels)
        self.fm_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.fm_matrix.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.fm_matrix.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )
        self.fm_matrix.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )

        self.fm_gridlayout.addWidget(self.fm_matrix, 1, 0)

        self.fm_matrix.resizeColumnsToContents()
        for f_i in range(6):
            for f_i2 in range(6):
                f_port = getattr(
                    sys.modules[__name__],
                    "FM1_OSC{}_FM{}".format(f_i2 + 1, f_i + 1))
                f_spinbox = spinbox_control(
                    None,
                    f_port,
                    self.plugin_rel_callback,
                    self.plugin_val_callback,
                    0,
                    100,
                    0,
                    KC_NONE,
                    self.port_dict,
                    self.preset_manager,
                    tooltip=(
                        'The amount of FM to apply to the destination \n'
                        'oscillator'
                    ),
                )
                f_spinbox.control.setFixedSize(
                    self.fm_matrix.columnWidth(f_i2),
                    self.fm_matrix.rowHeight(f_i),
                )
                self.fm_matrix.setCellWidget(f_i, f_i2, f_spinbox.control)
                self.fm_knobs.append(f_spinbox)


        self.fm_matrix_button = QPushButton(_("Menu"))

        self.fm_matrix_menu = QMenu(self.widget)
        self.fm_matrix_button.setMenu(self.fm_matrix_menu)
        f_origin_action = self.fm_matrix_menu.addAction(_("Set Origin"))
        f_origin_action.triggered.connect(self.set_fm_origin)
        f_return_action = self.fm_matrix_menu.addAction(_("Return to Origin"))
        f_return_action.triggered.connect(self.return_to_origin)
        self.fm_matrix_menu.addSeparator()
        f_macro1_action = self.fm_matrix_menu.addAction(_("Set Macro 1 End"))
        f_macro1_action.triggered.connect(self.set_fm_macro1_end)
        f_macro2_action = self.fm_matrix_menu.addAction(_("Set Macro 2 End"))
        f_macro2_action.triggered.connect(self.set_fm_macro2_end)
        self.fm_matrix_menu.addSeparator()
        f_return_macro1_action = self.fm_matrix_menu.addAction(
            _("Return to Macro 1 End"))
        f_return_macro1_action.triggered.connect(self.return_fm_macro1_end)
        f_return_macro2_action = self.fm_matrix_menu.addAction(
            _("Return to Macro 2 End"))
        f_return_macro2_action.triggered.connect(self.return_fm_macro2_end)
        self.fm_matrix_menu.addSeparator()
        f_clear_fm_action = self.fm_matrix_menu.addAction(_("Clear All"))
        f_clear_fm_action.triggered.connect(self.clear_all)

        self.fm_gridlayout.addWidget(
            QLabel(_("FM Modulation Macros")),
            0,
            1,
        )

        self.fm_macro_knobs_gridlayout = QGridLayout()
        self.fm_macro_knobs_gridlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
            10,
            10,
        )
        self.fm_macro_knobs_gridlayout.addWidget(self.fm_matrix_button, 0, 0)

        self.fm_gridlayout.addLayout(self.fm_macro_knobs_gridlayout, 1, 1)

        self.fm_macro_knobs = []
        self.osc_amp_mod_matrix_spinboxes = [[] for x in range(2)]

        for f_i in range(2):
            f_port = getattr(
                sys.modules[__name__],
                "FM1_FM_MACRO{}".format(f_i + 1),
            )
            f_macro = knob_control(
                f_knob_size,
                _("Macro{}".format(f_i + 1)),
                f_port,
                self.plugin_rel_callback,
                self.plugin_val_callback,
                0,
                100,
                0,
                KC_DECIMAL,
                self.port_dict,
                self.preset_manager,
                knob_kwargs=knob_kwargs,
                tooltip='Macros are used to morph between FM settings',
            )
            f_macro.add_to_grid_layout(
                self.fm_macro_knobs_gridlayout,
                f_i + 1,
            )
            self.fm_macro_knobs.append(f_macro)

            f_fm_macro_matrix = QTableWidget()
            self.fm_matrix.setEditTriggers(
                QAbstractItemView.EditTrigger.NoEditTriggers,
            )
            self.fm_matrix.setFocusPolicy(
                QtCore.Qt.FocusPolicy.NoFocus
            )
            self.fm_matrix.setSelectionMode(
                QAbstractItemView.SelectionMode.NoSelection
            )
            self.fm_gridlayout.addWidget(
                QLabel(
                    "Macro {}".format(f_i + 1),
                    f_fm_macro_matrix
                ),
                2,
                f_i,
            )

            f_fm_macro_matrix.setCornerButtonEnabled(False)
            f_fm_macro_matrix.setRowCount(7)
            f_fm_macro_matrix.setColumnCount(6)
            f_fm_macro_matrix.setFixedHeight(275)
            f_fm_src_matrix_labels = ["From Osc{}".format(x)
                for x in range(1, 7)] + ["Vol"]
            f_fm_dest_matrix_labels = ["To\nOsc{}".format(x)
                for x in range(1, 7)]
            f_fm_macro_matrix.setHorizontalHeaderLabels(
                f_fm_dest_matrix_labels,
            )
            f_fm_macro_matrix.setVerticalHeaderLabels(f_fm_src_matrix_labels)
            f_fm_macro_matrix.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
            f_fm_macro_matrix.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
            f_fm_macro_matrix.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Fixed,
            )
            f_fm_macro_matrix.verticalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Fixed,
            )

            self.fm_gridlayout.addWidget(f_fm_macro_matrix, 3, f_i)
            f_fm_macro_matrix.resizeColumnsToContents()

            for f_i2 in range(6):
                for f_i3 in range(6):
                    f_port = getattr(
                        sys.modules[__name__],
                        "FM1_FM_MACRO{}_OSC{}_FM{}".format(
                            f_i + 1, f_i3 + 1, f_i2 + 1))
                    f_spinbox = spinbox_control(
                        None,
                        f_port,
                        self.plugin_rel_callback,
                        self.plugin_val_callback,
                        -100,
                        100,
                        0,
                        KC_NONE,
                        self.port_dict,
                        self.preset_manager,
                        tooltip=(
                            'The amount of FM to apply to the\n'
                            'destination oscillator'
                        ),
                    )
                    f_spinbox.control.setFixedSize(
                        f_fm_macro_matrix.columnWidth(f_i3),
                        f_fm_macro_matrix.rowHeight(f_i2),
                    )
                    f_fm_macro_matrix.setCellWidget(
                        f_i2,
                        f_i3,
                        f_spinbox.control,
                    )
                    self.fm_macro_spinboxes[f_i].append(f_spinbox)

                f_port = getattr(
                    sys.modules[__name__],
                    "FM1_FM_MACRO{}_OSC{}_VOL".format(
                        f_i + 1,
                        f_i2 + 1,
                    ),
                )
                f_spinbox = spinbox_control(
                    None,
                    f_port,
                    self.plugin_rel_callback,
                    self.plugin_val_callback,
                    -100,
                    100,
                    0,
                    KC_NONE,
                    self.port_dict,
                    self.preset_manager,
                    tooltip=(
                        'The amount of FM to apply to the\n'
                        'destination oscillator'
                    ),
                )
                f_spinbox.control.setFixedSize(
                    f_fm_macro_matrix.columnWidth(f_i2),
                    f_fm_macro_matrix.rowHeight(6),
                )
                f_fm_macro_matrix.setCellWidget(6, f_i2, f_spinbox.control)
                self.osc_amp_mod_matrix_spinboxes[f_i].append(f_spinbox)

        ############################

        self.modulation_vlayout = QVBoxLayout(self.modulation_tab)

        self.hlayout_main = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout_main)
        self.main = main_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            FM1_MAIN_VOLUME,
            FM1_MAIN_GLIDE,
            FM1_MAIN_PITCHBEND_AMT,
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            a_poly_port=FM1_MONO_MODE,
            a_min_note_port=FM1_MIN_NOTE,
            a_max_note_port=FM1_MAX_NOTE,
            a_pitch_port=FM1_MAIN_PITCH,
            knob_kwargs=knob_kwargs,
        )
        knob_kwargs['arc_type'] = ArcType.BIDIRECTIONAL
        self.pan_knob = knob_control(
            f_knob_size,
            _("Pan"),
            FM1_MAIN_PAN,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip=(
                'Instrument pan.  Pan the entire plugin output left or right'
            ),
        )
        knob_kwargs.pop('arc_type')
        self.pan_knob.add_to_grid_layout(self.main.layout, 20)

        self.hlayout_main.addWidget(self.main.group_box)

        self.adsr_amp_main = ADSRMainWidget(
            f_knob_size,
            True,
            FM1_ATTACK_MAIN,
            FM1_ATTACK_MAIN_START,
            FM1_ATTACK_MAIN_END,
            FM1_DECAY_MAIN,
            FM1_DECAY_MAIN_START,
            FM1_DECAY_MAIN_END,
            FM1_SUSTAIN_MAIN,
            FM1_SUSTAIN_MAIN_START,
            FM1_SUSTAIN_MAIN_END,
            FM1_RELEASE_MAIN,
            FM1_RELEASE_MAIN_START,
            FM1_RELEASE_MAIN_END,
            _("AHDSR Main"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_prefx_port=FM1_ADSR_PREFX,
            a_knob_type=KC_LOG_TIME,
            a_hold_port=FM1_HOLD_MAIN,
            a_lin_port=FM1_ADSR_LIN_MAIN,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout_main.addWidget(self.adsr_amp_main.groupbox)

        self.perc_env = perc_env_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            FM1_PERC_ENV_TIME1,
            FM1_PERC_ENV_PITCH1,
            FM1_PERC_ENV_TIME2,
            FM1_PERC_ENV_PITCH2,
            FM1_PERC_ENV_ON,
            a_preset_mgr=self.preset_manager,
            knob_kwargs=knob_kwargs,
        )

        self.hlayout_main2 = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout_main2)
        self.hlayout_main2.addWidget(self.perc_env.groupbox)

        self.adsr_noise = adsr_widget(
            f_knob_size,
            True,
            FM1_ATTACK_NOISE,
            FM1_DECAY_NOISE,
            FM1_SUSTAIN_NOISE,
            FM1_RELEASE_NOISE,
            _("DAHDSR Noise"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_hold_port=FM1_HOLD_NOISE,
            a_delay_port=FM1_DELAY_NOISE,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout_main2.addWidget(self.adsr_noise.groupbox)
        self.adsr_noise_on = checkbox_control(
            "On",
            FM1_ADSR_NOISE_ON,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            tooltip='Enable the ADSR envelope for the noise generator',
        )
        self.adsr_noise_on.add_to_grid_layout(self.adsr_noise.layout, 21)

        self.groupbox_noise = QGroupBox(_("Noise"))
        self.groupbox_noise.setObjectName("plugin_groupbox")
        self.groupbox_noise_layout = QGridLayout(self.groupbox_noise)
        self.hlayout_main2.addWidget(self.groupbox_noise)
        self.noise_amp = knob_control(
            f_knob_size,
            _("Vol"),
            FM1_NOISE_AMP,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -60,
            0,
            -30,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='The volume of the noise generator',
        )
        self.noise_amp.add_to_grid_layout(self.groupbox_noise_layout, 0)

        self.noise_type = combobox_control(
            87,
            _("Type"),
            FM1_NOISE_TYPE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            [
                _("Off"),
                _("White"),
                _("Pink"),
                _('White Stereo'),
                _('Pink Stereo')
            ],
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            tooltip=(
                'Mono and stereo variants of white (flat spectrum), \n'
                'pink (sounds flat to the human ear) noise'
            ),
        )
        self.noise_type.control.setMaximumWidth(87)
        self.noise_type.add_to_grid_layout(self.groupbox_noise_layout, 1)

        self.noise_prefx = checkbox_control(
            "PreFX",
            FM1_NOISE_PREFX,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            a_preset_mgr=self.preset_manager,
            a_default=1,
            tooltip='If checked, noise is added before the effects section',
        )
        self.noise_prefx.add_to_grid_layout(self.groupbox_noise_layout, 6)

        self.modulation_vlayout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Policy.Expanding),
        )

        self.modulation_vlayout.addWidget(QLabel(_("PolyFX")))

        ############################

        self.main_layout = QVBoxLayout(self.poly_fx_tab)
        self.hlayout5 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout5)
        self.hlayout6 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout6)
        #From MultiFX
        self.fx0 = MultiFXSingle(
            _("FX0"),
            FM1_FX0_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout5.addWidget(self.fx0.group_box)
        self.fx1 = MultiFXSingle(
            _("FX1"),
            FM1_FX1_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout5.addWidget(self.fx1.group_box)
        self.fx2 = MultiFXSingle(
            _("FX2"),
            FM1_FX2_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout6.addWidget(self.fx2.group_box)
        self.fx3 = MultiFXSingle(
            _("FX3"),
            FM1_FX3_KNOB0,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_size=f_knob_size,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout6.addWidget(self.fx3.group_box)

        self.mod_matrix = QTableWidget()
        self.mod_matrix.setCornerButtonEnabled(False)
        self.mod_matrix.setRowCount(8)
        self.mod_matrix.setColumnCount(12)
        self.mod_matrix.setFixedHeight(291)
        self.mod_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.mod_matrix.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.mod_matrix.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )
        self.mod_matrix.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed,
        )
        f_hlabels = ["FX{}\nCtrl{}".format(x, y)
            for x in range(4) for y in range(1, 4)]
        self.mod_matrix.setHorizontalHeaderLabels(f_hlabels)
        self.mod_matrix.setVerticalHeaderLabels([
            _("DAHDSR 1"),
            _("DAHDSR 2"),
            _("Ramp Env"),
            _("LFO"),
            _("Pitch"),
            _("Velocity"),
            _("FM Macro 1"),
            _("FM Macro 2"),
        ])
        self.mod_matrix.resizeColumnsToContents()

        for f_i_dst in range(4):
            for f_i_src in range(8):
                for f_i_ctrl in range(3):
                    f_ctrl = spinbox_control(
                        None,
                        getattr(
                            sys.modules[__name__],
                            "FM1_PFXMATRIX_GRP0DST{}SRC{}CTRL{}".format(
                                f_i_dst, f_i_src, f_i_ctrl
                            )
                        ),
                        self.plugin_rel_callback,
                        self.plugin_val_callback,
                        -100,
                        100,
                        0,
                        KC_NONE,
                        self.port_dict,
                        self.preset_manager,
                        tooltip=(
                            'How much the modulation source affects the '
                            'destination'
                        ),
                    )
                    f_x = (f_i_dst * 3) + f_i_ctrl
                    f_ctrl.control.setFixedSize(
                        self.mod_matrix.columnWidth(f_x),
                        self.mod_matrix.rowHeight(f_i_src),
                    )
                    self.mod_matrix.setCellWidget(f_i_src, f_x, f_ctrl.control)

        self.main_layout.addWidget(self.mod_matrix)

        self.main_layout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Policy.Expanding),
        )

        self.hlayout7 = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout7)

        self.adsr_amp = adsr_widget(
            f_knob_size,
            True,
            FM1_ATTACK_PFX1,
            FM1_DECAY_PFX1,
            FM1_SUSTAIN_PFX1,
            FM1_RELEASE_PFX1,
            _("DAHDSR 1"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_delay_port=FM1_PFX_ADSR_DELAY,
            a_hold_port=FM1_PFX_ADSR_HOLD,
            knob_kwargs=knob_kwargs,
        )

        self.hlayout7.addWidget(self.adsr_amp.groupbox)

        self.adsr_filter = adsr_widget(
            f_knob_size,
            False,
            FM1_ATTACK_PFX2,
            FM1_DECAY_PFX2,
            FM1_SUSTAIN_PFX2,
            FM1_RELEASE_PFX2,
            _("DAHDSR 2"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_delay_port=FM1_PFX_ADSR_F_DELAY,
            a_hold_port=FM1_PFX_ADSR_F_HOLD,
            knob_kwargs=knob_kwargs,
        )
        self.hlayout7.addWidget(self.adsr_filter.groupbox)

        self.pitch_env = ramp_env_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            FM1_RAMP_ENV_TIME,
            FM1_PITCH_ENV_AMT,
            _("Ramp Env"),
            self.preset_manager,
            FM1_RAMP_CURVE,
            knob_kwargs=knob_kwargs,
        )
        self.pitch_env.amt_knob.name_label.setText(_("Pitch"))
        self.pitch_env.amt_knob.control.setRange(-60, 60)
        self.hlayout7.addWidget(self.pitch_env.groupbox)

        self.lfo = lfo_widget(
            f_knob_size,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            FM1_LFO_FREQ,
            FM1_LFO_TYPE,
            f_lfo_types,
            _("LFO"),
            self.preset_manager,
            FM1_LFO_PHASE,
            knob_kwargs=knob_kwargs,
        )

        self.lfo_hlayout = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.lfo_hlayout)
        self.lfo_hlayout.addWidget(self.lfo.groupbox)

        self.lfo_amount = knob_control(
            f_knob_size,
            _("Amount"),
            FM1_LFO_AMOUNT,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            0,
            100,
            100,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='The strength of LFO modulation',
        )
        self.lfo_amount.add_to_grid_layout(self.lfo.layout, 7)

        self.lfo_amp = knob_control(
            f_knob_size,
            _("Amp"),
            FM1_LFO_AMP,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -24,
            24,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Module the amplitude of the instrument',
        )
        self.lfo_amp.add_to_grid_layout(self.lfo.layout, 8)

        self.lfo_pitch = knob_control(
            f_knob_size,
            _("Pitch"),
            FM1_LFO_PITCH,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -36,
            36,
            0,
            KC_INTEGER,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Modulate the pitch of the instrument',
        )
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 9)

        self.lfo_pitch_fine = knob_control(
            f_knob_size,
            _("Fine"),
            FM1_LFO_PITCH_FINE,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            -100,
            100,
            0,
            KC_DECIMAL,
            self.port_dict,
            self.preset_manager,
            knob_kwargs=knob_kwargs,
            tooltip='Modulate the pitch of the instrument with fine control',
        )
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 10)

        self.adsr_lfo = adsr_widget(
            f_knob_size,
            False,
            FM1_ATTACK_LFO,
            FM1_DECAY_LFO,
            FM1_SUSTAIN_LFO,
            FM1_RELEASE_LFO,
            _("DAHDSR LFO"),
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_hold_port=FM1_HOLD_LFO,
            a_delay_port=FM1_DELAY_LFO,
            knob_kwargs=knob_kwargs,
        )
        self.lfo_hlayout.addWidget(self.adsr_lfo.groupbox)
        self.adsr_lfo_on = checkbox_control(
            "On",
            FM1_ADSR_LFO_ON,
            self.plugin_rel_callback,
            self.plugin_val_callback,
            self.port_dict,
            self.preset_manager,
            tooltip='Enable or disable the ADSR for the LFO',
        )
        self.adsr_lfo_on.add_to_grid_layout(self.adsr_lfo.layout, 21)

        self.additive_osc = custom_additive_oscillator(
            self.configure_plugin,
        )
        self.tab_widget.addTab(self.additive_osc.widget, "Additive")

        self.open_plugin_file()
        self.set_midi_learn(FM1_PORT_MAP)

    def open_plugin_file(self):
        AbstractPluginUI.open_plugin_file(self)
        self.set_fm_origin()

    def configure_plugin(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        self.configure_callback(self.plugin_uid, a_key, a_message)
        self.has_updated_controls = True

    def set_configure(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        if a_key.startswith("fm1_add_ui"):
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            self.additive_osc.set_values(int(a_key[-1]), f_arr)
        if a_key.startswith("fm1_add_phase"):
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            self.additive_osc.set_phases(int(a_key[-1]), f_arr)
        elif a_key.startswith("fm1_add_eng"):
            pass
        else:
            LOG.warning(f"FM1: Unknown configure message '{a_key}'")

    def reconfigure_plugin(self, a_dict):
        # Clear existing sample tables
        f_ui_config_keys = ["fm1_add_ui0", "fm1_add_ui1", "fm1_add_ui2"]
        f_eng_config_keys = ["fm1_add_eng0", "fm1_add_eng1", "fm1_add_eng2"]
        f_ui_phase_keys = ["fm1_add_phase0", "fm1_add_phase1",
                           "fm1_add_phase2"]
        f_empty_ui_val = "|".join(
            [str(ADDITIVE_OSC_MIN_AMP)] * ADDITIVE_OSC_HARMONIC_COUNT)
        f_empty_eng_val = "{}|{}".format(ADDITIVE_WAVETABLE_SIZE,
            "|".join(["0.0"] * ADDITIVE_WAVETABLE_SIZE))
        for f_key in (f_ui_config_keys + f_ui_phase_keys):
            if f_key in a_dict:
                self.configure_plugin(f_key, a_dict[f_key])
                self.set_configure(f_key, a_dict[f_key])
            else:
                self.configure_plugin(f_key, f_empty_ui_val)
                self.set_configure(f_key, f_empty_ui_val)
        for f_key in f_eng_config_keys:
            if f_key in a_dict:
                self.configure_plugin(f_key, a_dict[f_key])
            else:
                self.configure_plugin(f_key, f_empty_eng_val)
        self.has_updated_controls = True

    def set_fm_origin(self):
        self.fm_origin = []
        for f_knob in self.fm_knobs:
            self.fm_origin.append(f_knob.get_value())

    def return_to_origin(self):
        for f_value, f_knob in zip(self.fm_origin, self.fm_knobs):
            f_knob.set_value(f_value, True)
        self.reset_fm_macro_knobs()

    def reset_fm_macro_knobs(self):
        for f_knob in self.fm_macro_knobs:
            f_knob.set_value(0, True)

    def set_fm_macro1_end(self):
        self.set_fm_macro_end(0)

    def set_fm_macro2_end(self):
        self.set_fm_macro_end(1)

    def set_fm_macro_end(self, a_index):
        for f_spinbox, f_knob, f_origin in zip(
        self.fm_macro_spinboxes[a_index], self.fm_knobs, self.fm_origin):
            f_value = f_knob.get_value() - f_origin
            f_value = clip_value(f_value, -100, 100)
            f_spinbox.set_value(f_value, True)

    def clear_all(self):
        for f_control in (
        self.fm_knobs + self.fm_macro_spinboxes[0] +
        self.fm_macro_spinboxes[1]):
            f_control.set_value(0, True)

    def return_fm_macro1_end(self):
        self.return_fm_macro_end(0)

    def return_fm_macro2_end(self):
        self.return_fm_macro_end(1)

    def return_fm_macro_end(self, a_index):
        for f_spinbox, f_knob, f_origin in zip(
        self.fm_macro_spinboxes[a_index], self.fm_knobs, self.fm_origin):
            f_value = f_spinbox.get_value() + f_origin
            f_value = clip_value(f_value, 0, 100)
            f_knob.set_value(f_value, True)
        self.reset_fm_macro_knobs()

