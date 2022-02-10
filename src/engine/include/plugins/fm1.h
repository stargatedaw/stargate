/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef FM1_PLUGIN_H
#define FM1_PLUGIN_H

#include "audiodsp/constants.h"
#include "audiodsp/lib/osc_core.h"
#include "audiodsp/lib/pitch_core.h"
#include "audiodsp/lib/resampler_linear.h"
#include "audiodsp/lib/smoother-linear.h"
#include "audiodsp/lib/voice.h"
#include "audiodsp/modules/distortion/clipper.h"
#include "audiodsp/modules/filter/svf.h"
#include "audiodsp/modules/modulation/adsr.h"
#include "audiodsp/modules/modulation/perc_env.h"
#include "audiodsp/modules/modulation/ramp_env.h"
#include "audiodsp/modules/multifx/multifx3knob.h"
#include "audiodsp/modules/oscillator/lfo_simple.h"
#include "audiodsp/modules/oscillator/noise.h"
#include "audiodsp/modules/oscillator/osc_simple.h"
#include "audiodsp/modules/oscillator/osc_wavetable.h"
#include "audiodsp/modules/oscillator/wavetables.h"
#include "audiodsp/modules/signal_routing/audio_xfade.h"
#include "audiodsp/modules/signal_routing/panner2.h"
#include "plugin.h"
#include "compiler.h"

/*Total number of LFOs, ADSRs, other envelopes, etc...
 * Used for the PolyFX mod matrix*/
#define FM1_MODULATOR_COUNT 8
//How many modular PolyFX
#define FM1_MODULAR_POLYFX_COUNT 4
#define FM1_CONTROLS_PER_MOD_EFFECT 3

#define FM1_FM_MACRO_COUNT 2

#define FM1_OSC_COUNT 6

//How many modular PolyFX
#define FM1_MODULAR_POLYFX_COUNT 4
//How many ports per PolyFX, 3 knobs and a combobox
#define FM1_PORTS_PER_MOD_EFFECT 4
//How many knobs per PolyFX, 3 knobs


#define FM1_OUTPUT0  0
#define FM1_OUTPUT1  1

#define FM1_FIRST_CONTROL_PORT 2
#define FM1_ATTACK_MAIN  2
#define FM1_DECAY_MAIN   3
#define FM1_SUSTAIN_MAIN 4
#define FM1_RELEASE_MAIN 5
#define FM1_NOISE_AMP 6
#define FM1_OSC1_TYPE 7
#define FM1_OSC1_PITCH 8
#define FM1_OSC1_TUNE 9
#define FM1_OSC1_VOLUME 10
#define FM1_OSC2_TYPE 11
#define FM1_OSC2_PITCH 12
#define FM1_OSC2_TUNE 13
#define FM1_OSC2_VOLUME 14
#define FM1_MAIN_VOLUME 15
#define FM1_OSC1_UNISON_VOICES 16
#define FM1_OSC1_UNISON_SPREAD 17
#define FM1_MAIN_GLIDE 18
#define FM1_MAIN_PITCHBEND_AMT 19
#define FM1_ATTACK1  20
#define FM1_DECAY1   21
#define FM1_SUSTAIN1 22
#define FM1_RELEASE1 23
#define FM1_ATTACK2  24
#define FM1_DECAY2   25
#define FM1_SUSTAIN2 26
#define FM1_RELEASE2 27
#define FM1_ATTACK_PFX1  28
#define FM1_DECAY_PFX1   29
#define FM1_SUSTAIN_PFX1 30
#define FM1_RELEASE_PFX1 31
#define FM1_ATTACK_PFX2  32
#define FM1_DECAY_PFX2   33
#define FM1_SUSTAIN_PFX2 34
#define FM1_RELEASE_PFX2 35
#define FM1_NOISE_TYPE 36
#define FM1_RAMP_ENV_TIME 37
#define FM1_LFO_FREQ 38
#define FM1_LFO_TYPE 39
#define FM1_FX0_KNOB0  40
#define FM1_FX0_KNOB1 41
#define FM1_FX0_KNOB2  42
#define FM1_FX0_COMBOBOX 43
#define FM1_FX1_KNOB0  44
#define FM1_FX1_KNOB1  45
#define FM1_FX1_KNOB2  46
#define FM1_FX1_COMBOBOX 47
#define FM1_FX2_KNOB0  48
#define FM1_FX2_KNOB1  49
#define FM1_FX2_KNOB2  50
#define FM1_FX2_COMBOBOX 51
#define FM1_FX3_KNOB0  52
#define FM1_FX3_KNOB1  53
#define FM1_FX3_KNOB2  54
#define FM1_FX3_COMBOBOX 55
//PolyFX Mod Matrix
#define FM1_PFXMATRIX_FIRST_PORT 56

#define FM1_PFXMATRIX_GRP0DST0SRC0CTRL0  56
#define FM1_PFXMATRIX_GRP0DST0SRC0CTRL1  57
#define FM1_PFXMATRIX_GRP0DST0SRC0CTRL2  58
#define FM1_PFXMATRIX_GRP0DST0SRC1CTRL0  59
#define FM1_PFXMATRIX_GRP0DST0SRC1CTRL1  60
#define FM1_PFXMATRIX_GRP0DST0SRC1CTRL2  61
#define FM1_PFXMATRIX_GRP0DST0SRC2CTRL0  62
#define FM1_PFXMATRIX_GRP0DST0SRC2CTRL1  63
#define FM1_PFXMATRIX_GRP0DST0SRC2CTRL2  64
#define FM1_PFXMATRIX_GRP0DST0SRC3CTRL0  65
#define FM1_PFXMATRIX_GRP0DST0SRC3CTRL1  66
#define FM1_PFXMATRIX_GRP0DST0SRC3CTRL2  67
#define FM1_PFXMATRIX_GRP0DST1SRC0CTRL0  68
#define FM1_PFXMATRIX_GRP0DST1SRC0CTRL1  69
#define FM1_PFXMATRIX_GRP0DST1SRC0CTRL2  70
#define FM1_PFXMATRIX_GRP0DST1SRC1CTRL0  71
#define FM1_PFXMATRIX_GRP0DST1SRC1CTRL1  72
#define FM1_PFXMATRIX_GRP0DST1SRC1CTRL2  73
#define FM1_PFXMATRIX_GRP0DST1SRC2CTRL0  74
#define FM1_PFXMATRIX_GRP0DST1SRC2CTRL1  75
#define FM1_PFXMATRIX_GRP0DST1SRC2CTRL2  76
#define FM1_PFXMATRIX_GRP0DST1SRC3CTRL0  77
#define FM1_PFXMATRIX_GRP0DST1SRC3CTRL1  78
#define FM1_PFXMATRIX_GRP0DST1SRC3CTRL2  79
#define FM1_PFXMATRIX_GRP0DST2SRC0CTRL0  80
#define FM1_PFXMATRIX_GRP0DST2SRC0CTRL1  81
#define FM1_PFXMATRIX_GRP0DST2SRC0CTRL2  82
#define FM1_PFXMATRIX_GRP0DST2SRC1CTRL0  83
#define FM1_PFXMATRIX_GRP0DST2SRC1CTRL1  84
#define FM1_PFXMATRIX_GRP0DST2SRC1CTRL2  85
#define FM1_PFXMATRIX_GRP0DST2SRC2CTRL0  86
#define FM1_PFXMATRIX_GRP0DST2SRC2CTRL1  87
#define FM1_PFXMATRIX_GRP0DST2SRC2CTRL2  88
#define FM1_PFXMATRIX_GRP0DST2SRC3CTRL0  89
#define FM1_PFXMATRIX_GRP0DST2SRC3CTRL1  90
#define FM1_PFXMATRIX_GRP0DST2SRC3CTRL2  91
#define FM1_PFXMATRIX_GRP0DST3SRC0CTRL0  92
#define FM1_PFXMATRIX_GRP0DST3SRC0CTRL1  93
#define FM1_PFXMATRIX_GRP0DST3SRC0CTRL2  94
#define FM1_PFXMATRIX_GRP0DST3SRC1CTRL0  95
#define FM1_PFXMATRIX_GRP0DST3SRC1CTRL1  96
#define FM1_PFXMATRIX_GRP0DST3SRC1CTRL2  97
#define FM1_PFXMATRIX_GRP0DST3SRC2CTRL0  98
#define FM1_PFXMATRIX_GRP0DST3SRC2CTRL1  99
#define FM1_PFXMATRIX_GRP0DST3SRC2CTRL2  100
#define FM1_PFXMATRIX_GRP0DST3SRC3CTRL0  101
#define FM1_PFXMATRIX_GRP0DST3SRC3CTRL1  102
#define FM1_PFXMATRIX_GRP0DST3SRC3CTRL2  103

//End PolyFX Mod Matrix

#define FM1_ADSR1_CHECKBOX 105
#define FM1_ADSR2_CHECKBOX 106
#define FM1_LFO_AMP 107
#define FM1_LFO_PITCH 108
#define FM1_PITCH_ENV_AMT 109
#define FM1_OSC2_UNISON_VOICES 110
#define FM1_OSC2_UNISON_SPREAD 111
#define FM1_LFO_AMOUNT 112
#define FM1_OSC3_TYPE 113
#define FM1_OSC3_PITCH 114
#define FM1_OSC3_TUNE 115
#define FM1_OSC3_VOLUME 116
#define FM1_OSC3_UNISON_VOICES 117
#define FM1_OSC3_UNISON_SPREAD 118
#define FM1_OSC1_FM1 119
#define FM1_OSC1_FM2 120
#define FM1_OSC1_FM3 121
#define FM1_OSC2_FM1 122
#define FM1_OSC2_FM2 123
#define FM1_OSC2_FM3 124
#define FM1_OSC3_FM1 125
#define FM1_OSC3_FM2 126
#define FM1_OSC3_FM3 127
#define FM1_ATTACK3  128
#define FM1_DECAY3   129
#define FM1_SUSTAIN3 130
#define FM1_RELEASE3 131
#define FM1_ADSR3_CHECKBOX 132

#define FM1_PFXMATRIX_GRP0DST0SRC4CTRL0  133
#define FM1_PFXMATRIX_GRP0DST0SRC4CTRL1  134
#define FM1_PFXMATRIX_GRP0DST0SRC4CTRL2  135
#define FM1_PFXMATRIX_GRP0DST1SRC4CTRL0  136
#define FM1_PFXMATRIX_GRP0DST1SRC4CTRL1  137
#define FM1_PFXMATRIX_GRP0DST1SRC4CTRL2  138
#define FM1_PFXMATRIX_GRP0DST2SRC4CTRL0  139
#define FM1_PFXMATRIX_GRP0DST2SRC4CTRL1  140
#define FM1_PFXMATRIX_GRP0DST2SRC4CTRL2  141
#define FM1_PFXMATRIX_GRP0DST3SRC4CTRL0  142
#define FM1_PFXMATRIX_GRP0DST3SRC4CTRL1  143
#define FM1_PFXMATRIX_GRP0DST3SRC4CTRL2  144

#define FM1_PFXMATRIX_GRP0DST0SRC5CTRL0  145
#define FM1_PFXMATRIX_GRP0DST0SRC5CTRL1  146
#define FM1_PFXMATRIX_GRP0DST0SRC5CTRL2  147
#define FM1_PFXMATRIX_GRP0DST1SRC5CTRL0  148
#define FM1_PFXMATRIX_GRP0DST1SRC5CTRL1  149
#define FM1_PFXMATRIX_GRP0DST1SRC5CTRL2  150
#define FM1_PFXMATRIX_GRP0DST2SRC5CTRL0  151
#define FM1_PFXMATRIX_GRP0DST2SRC5CTRL1  152
#define FM1_PFXMATRIX_GRP0DST2SRC5CTRL2  153
#define FM1_PFXMATRIX_GRP0DST3SRC5CTRL0  154
#define FM1_PFXMATRIX_GRP0DST3SRC5CTRL1  155
#define FM1_PFXMATRIX_GRP0DST3SRC5CTRL2  156

#define FM1_PERC_ENV_TIME1 157
#define FM1_PERC_ENV_PITCH1 158
#define FM1_PERC_ENV_TIME2 159
#define FM1_PERC_ENV_PITCH2 160
#define FM1_PERC_ENV_ON 161
#define FM1_RAMP_CURVE 162
#define FM1_MONO_MODE 163

#define FM1_OSC4_TYPE 164
#define FM1_OSC4_PITCH 165
#define FM1_OSC4_TUNE 166
#define FM1_OSC4_VOLUME 167
#define FM1_OSC4_UNISON_VOICES 168
#define FM1_OSC4_UNISON_SPREAD 169
#define FM1_OSC1_FM4 170
#define FM1_OSC2_FM4 171
#define FM1_OSC3_FM4 172
#define FM1_OSC4_FM1 173
#define FM1_OSC4_FM2 174
#define FM1_OSC4_FM3 175
#define FM1_OSC4_FM4 176
#define FM1_ATTACK4  177
#define FM1_DECAY4   178
#define FM1_SUSTAIN4 179
#define FM1_RELEASE4 180
#define FM1_ADSR4_CHECKBOX 181

#define FM1_FM_MACRO1 182
#define FM1_FM_MACRO1_OSC1_FM1 183
#define FM1_FM_MACRO1_OSC1_FM2 184
#define FM1_FM_MACRO1_OSC1_FM3 185
#define FM1_FM_MACRO1_OSC1_FM4 186
#define FM1_FM_MACRO1_OSC2_FM1 187
#define FM1_FM_MACRO1_OSC2_FM2 188
#define FM1_FM_MACRO1_OSC2_FM3 189
#define FM1_FM_MACRO1_OSC2_FM4 190
#define FM1_FM_MACRO1_OSC3_FM1 191
#define FM1_FM_MACRO1_OSC3_FM2 192
#define FM1_FM_MACRO1_OSC3_FM3 193
#define FM1_FM_MACRO1_OSC3_FM4 194
#define FM1_FM_MACRO1_OSC4_FM1 195
#define FM1_FM_MACRO1_OSC4_FM2 196
#define FM1_FM_MACRO1_OSC4_FM3 197
#define FM1_FM_MACRO1_OSC4_FM4 198

#define FM1_FM_MACRO2 199
#define FM1_FM_MACRO2_OSC1_FM1 200
#define FM1_FM_MACRO2_OSC1_FM2 201
#define FM1_FM_MACRO2_OSC1_FM3 202
#define FM1_FM_MACRO2_OSC1_FM4 203
#define FM1_FM_MACRO2_OSC2_FM1 204
#define FM1_FM_MACRO2_OSC2_FM2 205
#define FM1_FM_MACRO2_OSC2_FM3 206
#define FM1_FM_MACRO2_OSC2_FM4 207
#define FM1_FM_MACRO2_OSC3_FM1 208
#define FM1_FM_MACRO2_OSC3_FM2 209
#define FM1_FM_MACRO2_OSC3_FM3 210
#define FM1_FM_MACRO2_OSC3_FM4 211
#define FM1_FM_MACRO2_OSC4_FM1 212
#define FM1_FM_MACRO2_OSC4_FM2 213
#define FM1_FM_MACRO2_OSC4_FM3 214
#define FM1_FM_MACRO2_OSC4_FM4 215

#define FM1_LFO_PHASE 216

#define FM1_FM_MACRO1_OSC1_VOL 217
#define FM1_FM_MACRO1_OSC2_VOL 218
#define FM1_FM_MACRO1_OSC3_VOL 219
#define FM1_FM_MACRO1_OSC4_VOL 220

#define FM1_FM_MACRO2_OSC1_VOL 221
#define FM1_FM_MACRO2_OSC2_VOL 222
#define FM1_FM_MACRO2_OSC3_VOL 223
#define FM1_FM_MACRO2_OSC4_VOL 224
#define FM1_LFO_PITCH_FINE 225
#define FM1_ADSR_PREFX 226

#define FM1_ADSR1_DELAY 227
#define FM1_ADSR2_DELAY 228
#define FM1_ADSR3_DELAY 229
#define FM1_ADSR4_DELAY 230

#define FM1_ADSR1_HOLD 231
#define FM1_ADSR2_HOLD 232
#define FM1_ADSR3_HOLD 233
#define FM1_ADSR4_HOLD 234

#define FM1_PFX_ADSR_DELAY 235
#define FM1_PFX_ADSR_F_DELAY 236

#define FM1_PFX_ADSR_HOLD 237
#define FM1_PFX_ADSR_F_HOLD 238

#define FM1_HOLD_MAIN  239

#define FM1_DELAY_NOISE  240
#define FM1_ATTACK_NOISE  241
#define FM1_HOLD_NOISE  242
#define FM1_DECAY_NOISE   243
#define FM1_SUSTAIN_NOISE 244
#define FM1_RELEASE_NOISE 245
#define FM1_ADSR_NOISE_ON 246

#define FM1_DELAY_LFO  247
#define FM1_ATTACK_LFO  248
#define FM1_HOLD_LFO  249
#define FM1_DECAY_LFO   250
#define FM1_SUSTAIN_LFO 251
#define FM1_RELEASE_LFO 252
#define FM1_ADSR_LFO_ON 253

#define FM1_OSC5_TYPE 254
#define FM1_OSC5_PITCH 255
#define FM1_OSC5_TUNE 256
#define FM1_OSC5_VOLUME 257
#define FM1_OSC5_UNISON_VOICES 258
#define FM1_OSC5_UNISON_SPREAD 259
#define FM1_OSC1_FM5 260
#define FM1_OSC2_FM5 261
#define FM1_OSC3_FM5 262
#define FM1_OSC4_FM5 263
#define FM1_OSC5_FM5 264
#define FM1_OSC6_FM5 265
#define FM1_ADSR5_DELAY 266
#define FM1_ATTACK5  267
#define FM1_ADSR5_HOLD 268
#define FM1_DECAY5   269
#define FM1_SUSTAIN5 270
#define FM1_RELEASE5 271
#define FM1_ADSR5_CHECKBOX 272

#define FM1_OSC6_TYPE 273
#define FM1_OSC6_PITCH 274
#define FM1_OSC6_TUNE 275
#define FM1_OSC6_VOLUME 276
#define FM1_OSC6_UNISON_VOICES 277
#define FM1_OSC6_UNISON_SPREAD 278
#define FM1_OSC1_FM6 279
#define FM1_OSC2_FM6 280
#define FM1_OSC3_FM6 281
#define FM1_OSC4_FM6 282
#define FM1_OSC5_FM6 283
#define FM1_OSC6_FM6 284
#define FM1_ADSR6_DELAY 285
#define FM1_ATTACK6 286
#define FM1_ADSR6_HOLD 287
#define FM1_DECAY6   288
#define FM1_SUSTAIN6 289
#define FM1_RELEASE6 290
#define FM1_ADSR6_CHECKBOX 291


#define FM1_FM_MACRO1_OSC1_FM5 292
#define FM1_FM_MACRO1_OSC2_FM5 293
#define FM1_FM_MACRO1_OSC3_FM5 294
#define FM1_FM_MACRO1_OSC4_FM5 295
#define FM1_FM_MACRO1_OSC5_FM5 296
#define FM1_FM_MACRO1_OSC6_FM5 297

#define FM1_FM_MACRO1_OSC1_FM6 298
#define FM1_FM_MACRO1_OSC2_FM6 299
#define FM1_FM_MACRO1_OSC3_FM6 300
#define FM1_FM_MACRO1_OSC4_FM6 301
#define FM1_FM_MACRO1_OSC5_FM6 302
#define FM1_FM_MACRO1_OSC6_FM6 303

#define FM1_FM_MACRO1_OSC5_FM1 304
#define FM1_FM_MACRO1_OSC5_FM2 305
#define FM1_FM_MACRO1_OSC5_FM3 306
#define FM1_FM_MACRO1_OSC5_FM4 307

#define FM1_FM_MACRO1_OSC6_FM1 308
#define FM1_FM_MACRO1_OSC6_FM2 309
#define FM1_FM_MACRO1_OSC6_FM3 310
#define FM1_FM_MACRO1_OSC6_FM4 311

#define FM1_FM_MACRO1_OSC5_VOL 312
#define FM1_FM_MACRO1_OSC6_VOL 313

#define FM1_FM_MACRO2_OSC1_FM5 314
#define FM1_FM_MACRO2_OSC2_FM5 315
#define FM1_FM_MACRO2_OSC3_FM5 316
#define FM1_FM_MACRO2_OSC4_FM5 317
#define FM1_FM_MACRO2_OSC5_FM5 318
#define FM1_FM_MACRO2_OSC6_FM5 319

#define FM1_FM_MACRO2_OSC1_FM6 320
#define FM1_FM_MACRO2_OSC2_FM6 321
#define FM1_FM_MACRO2_OSC3_FM6 322
#define FM1_FM_MACRO2_OSC4_FM6 323
#define FM1_FM_MACRO2_OSC5_FM6 324
#define FM1_FM_MACRO2_OSC6_FM6 325

#define FM1_FM_MACRO2_OSC5_FM1 326
#define FM1_FM_MACRO2_OSC5_FM2 327
#define FM1_FM_MACRO2_OSC5_FM3 328
#define FM1_FM_MACRO2_OSC5_FM4 329

#define FM1_FM_MACRO2_OSC6_FM1 330
#define FM1_FM_MACRO2_OSC6_FM2 331
#define FM1_FM_MACRO2_OSC6_FM3 332
#define FM1_FM_MACRO2_OSC6_FM4 333

#define FM1_FM_MACRO2_OSC5_VOL 334
#define FM1_FM_MACRO2_OSC6_VOL 335

#define FM1_OSC5_FM1 336
#define FM1_OSC5_FM2 337
#define FM1_OSC5_FM3 338
#define FM1_OSC5_FM4 339

#define FM1_OSC6_FM1 340
#define FM1_OSC6_FM2 341
#define FM1_OSC6_FM3 342
#define FM1_OSC6_FM4 343
#define FM1_NOISE_PREFX 344

#define FM1_PFXMATRIX_GRP0DST0SRC6CTRL0 345
#define FM1_PFXMATRIX_GRP0DST0SRC6CTRL1 346
#define FM1_PFXMATRIX_GRP0DST0SRC6CTRL2 347
#define FM1_PFXMATRIX_GRP0DST1SRC6CTRL0 348
#define FM1_PFXMATRIX_GRP0DST1SRC6CTRL1 349
#define FM1_PFXMATRIX_GRP0DST1SRC6CTRL2 350
#define FM1_PFXMATRIX_GRP0DST2SRC6CTRL0 351
#define FM1_PFXMATRIX_GRP0DST2SRC6CTRL1 352
#define FM1_PFXMATRIX_GRP0DST2SRC6CTRL2 353
#define FM1_PFXMATRIX_GRP0DST3SRC6CTRL0 354
#define FM1_PFXMATRIX_GRP0DST3SRC6CTRL1 355
#define FM1_PFXMATRIX_GRP0DST3SRC6CTRL2 356

#define FM1_PFXMATRIX_GRP0DST0SRC7CTRL0 357
#define FM1_PFXMATRIX_GRP0DST0SRC7CTRL1 358
#define FM1_PFXMATRIX_GRP0DST0SRC7CTRL2 359
#define FM1_PFXMATRIX_GRP0DST1SRC7CTRL0 360
#define FM1_PFXMATRIX_GRP0DST1SRC7CTRL1 361
#define FM1_PFXMATRIX_GRP0DST1SRC7CTRL2 362
#define FM1_PFXMATRIX_GRP0DST2SRC7CTRL0 363
#define FM1_PFXMATRIX_GRP0DST2SRC7CTRL1 364
#define FM1_PFXMATRIX_GRP0DST2SRC7CTRL2 365
#define FM1_PFXMATRIX_GRP0DST3SRC7CTRL0 366
#define FM1_PFXMATRIX_GRP0DST3SRC7CTRL1 367
#define FM1_PFXMATRIX_GRP0DST3SRC7CTRL2 368

#define FM1_MIN_NOTE 369
#define FM1_MAX_NOTE 370
#define FM1_MAIN_PITCH 371
#define FM1_ADSR_LIN_MAIN 372
#define FM1_MAIN_PAN 373
#define FM1_OSC1_PAN 374
#define FM1_OSC2_PAN 375
#define FM1_OSC3_PAN 376
#define FM1_OSC4_PAN 377
#define FM1_OSC5_PAN 378
#define FM1_OSC6_PAN 379

#define FM1_ATTACK_MAIN_START 380
#define FM1_ATTACK_MAIN_END 381
#define FM1_DECAY_MAIN_START 382
#define FM1_DECAY_MAIN_END 383
#define FM1_SUSTAIN_MAIN_START 384
#define FM1_SUSTAIN_MAIN_END 385
#define FM1_RELEASE_MAIN_START 386
#define FM1_RELEASE_MAIN_END 387

/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define FM1_COUNT 388

#define FM1_POLYPHONY 24
#define FM1_POLYPHONY_THRESH 12

typedef struct {
    t_wt_wavetables * wavetables;
    t_smoother_linear pitchbend_smoother;
    t_smoother_linear fm_macro_smoother[FM1_FM_MACRO_COUNT];
    int reset_wavetables;
    t_svf2_filter aa_filter;
    t_smoother_linear pan_smoother;
    t_pn2_panner2 panner;
}t_fm1_mono_modules;

typedef struct{
    SGFLT fm_osc_values[FM1_OSC_COUNT];
    SGFLT fm_last;

    SGFLT osc_linamp;
    int osc_audible;
    int osc_on;
    SGFLT osc_uni_spread;
    SGFLT osc_fm[FM1_OSC_COUNT];
    SGFLT osc_macro_amp[2];

    t_osc_wav_unison osc_wavtable;

    t_adsr adsr_amp_osc;
    int adsr_amp_on;
    t_pn2_panner2 panner;
} t_fm1_osc;

typedef struct {
    t_mf3_multi multieffect;
    fp_mf3_run fx_func_ptr;
} t_fm1_pfx_group;

typedef struct {
    fp_adsr_run adsr_run_func;
    t_adsr adsr_main;
    /*This corresponds to the current sample being processed on this voice.
     * += this to the output buffer when finished.*/
    struct ResamplerStereoPair current_sample;
    t_ramp_env glide_env;
    t_adsr adsr_amp;
    t_adsr adsr_filter;
    t_ramp_env ramp_env;

    int adsr_lfo_on;
    t_lfs_lfo lfo1;
    SGFLT lfo_amount_output, lfo_amp_output, lfo_pitch_output;
    t_adsr adsr_lfo;

    SGFLT note_f;
    int note;

    t_smoother_linear glide_smoother;

    //base pitch for all oscillators, to avoid redundant calculations
    SGFLT base_pitch;
    SGFLT target_pitch;
    //For simplicity, this is used whether glide is turned on or not
    SGFLT last_pitch;

    struct ResamplerLinear resampler;

    int perc_env_on;
    t_pnv_perc_env perc_env;

    t_fm1_osc osc[FM1_OSC_COUNT];

    SGFLT noise_amp;
    SGFLT noise_linamp;
    fp_noise_stereo noise_func_ptr;
    t_white_noise white_noise[2];
    SGFLT noise_sample;
    t_adsr adsr_noise;
    int adsr_noise_on;
    int noise_prefx;

    int adsr_prefx;

    SGFLT velocity_track;
    SGFLT keyboard_track;

    t_fm1_pfx_group effects[FM1_MODULAR_POLYFX_COUNT];

    SGFLT multifx_current_sample[2];
    SGFLT * modulator_outputs[FM1_MODULATOR_COUNT];

    SGFLT amp;
    t_pn2_panner2 panner;
    SGFLT main_vol_lin;

    int active_polyfx[FM1_MODULAR_POLYFX_COUNT];
    int active_polyfx_count;

    //The index of the control to mod, currently 0-2
    int polyfx_mod_ctrl_indexes[FM1_MODULAR_POLYFX_COUNT]
        [(FM1_CONTROLS_PER_MOD_EFFECT * FM1_MODULATOR_COUNT)];

    //How many polyfx_mod_ptrs to iterate through for the current note
    int polyfx_mod_counts[FM1_MODULAR_POLYFX_COUNT];

    //The index of the modulation source(LFO, ADSR, etc...) to multiply by
    int polyfx_mod_src_index[FM1_MODULAR_POLYFX_COUNT]
    [(FM1_CONTROLS_PER_MOD_EFFECT * FM1_MODULATOR_COUNT)];

    //The value of the mod_matrix knob, multiplied by .01
    SGFLT polyfx_mod_matrix_values[FM1_MODULAR_POLYFX_COUNT]
    [(FM1_CONTROLS_PER_MOD_EFFECT * FM1_MODULATOR_COUNT)];

} t_fm1_poly_voice;

struct FM1OscControl {
    PluginData *attack;
    PluginData *decay;
    PluginData *sustain;
    PluginData *release;

    PluginData *adsr_checked;

    PluginData *adsr_fm_delay;
    PluginData *adsr_fm_hold;

    PluginData *pitch;
    PluginData *tune;
    PluginData *vol;
    PluginData *type;
    PluginData *uni_voice;
    PluginData *uni_spread;
    PluginData *pan;

    PluginData *fm[FM1_OSC_COUNT];
};

typedef struct {
    char pad1[CACHE_LINE_SIZE];
    PluginData *adsr_lin_main;
    PluginData *attack_main;
    PluginData *attack_main_start;
    PluginData *attack_main_end;
    PluginData *hold_main;
    PluginData *decay_main;
    PluginData *decay_main_start;
    PluginData *decay_main_end;
    PluginData *sustain_main;
    PluginData *sustain_main_start;
    PluginData *sustain_main_end;
    PluginData *release_main;
    PluginData *release_main_start;
    PluginData *release_main_end;

    struct FM1OscControl osc[FM1_OSC_COUNT];

    PluginData *main_vol;
    PluginData *pan;

    PluginData *pfx_delay;
    PluginData *pfx_attack;
    PluginData *pfx_hold;
    PluginData *pfx_decay;
    PluginData *pfx_sustain;
    PluginData *pfx_release;

    PluginData *pfx_delay_f;
    PluginData *pfx_attack_f;
    PluginData *pfx_hold_f;
    PluginData *pfx_decay_f;
    PluginData *pfx_sustain_f;
    PluginData *pfx_release_f;

    PluginData *noise_amp;
    PluginData *noise_type;

    PluginData *noise_adsr_on;
    PluginData *noise_prefx;
    PluginData *noise_delay;
    PluginData *noise_attack;
    PluginData *noise_hold;
    PluginData *noise_decay;
    PluginData *noise_sustain;
    PluginData *noise_release;

    PluginData *main_glide;
    PluginData *main_pb_amt;

    PluginData *pitch_env_time;
    PluginData *pitch_env_amt;
    PluginData *ramp_curve;

    PluginData *lfo_freq;
    PluginData *lfo_type;
    PluginData *lfo_phase;

    PluginData *lfo_amp;
    PluginData *lfo_pitch;
    PluginData *lfo_pitch_fine;
    PluginData *lfo_amount;

    PluginData *lfo_adsr_on;
    PluginData *lfo_delay;
    PluginData *lfo_attack;
    PluginData *lfo_hold;
    PluginData *lfo_decay;
    PluginData *lfo_sustain;
    PluginData *lfo_release;

    PluginData *perc_env_time1;
    PluginData *perc_env_pitch1;
    PluginData *perc_env_time2;
    PluginData *perc_env_pitch2;
    PluginData *perc_env_on;
    PluginData *adsr_prefx;

    PluginData *fm_macro[2];
    PluginData *fm_macro_values[2][FM1_OSC_COUNT][FM1_OSC_COUNT];
    PluginData *amp_macro_values[2][FM1_OSC_COUNT];

    PluginData *mono_mode;

    PluginData *min_note;
    PluginData *max_note;
    PluginData *main_pitch;

    //Corresponds to the actual knobs on the effects themselves,
    //not the mod matrix
    PluginData *pfx_mod_knob
        [FM1_MODULAR_POLYFX_COUNT]
        [FM1_CONTROLS_PER_MOD_EFFECT];

    PluginData *fx_combobox[FM1_MODULAR_POLYFX_COUNT];

    //PolyFX Mod Matrix
    //Corresponds to the mod matrix spinboxes
    PluginData *polyfx_mod_matrix
        [FM1_MODULAR_POLYFX_COUNT]
        [FM1_MODULATOR_COUNT]
        [FM1_CONTROLS_PER_MOD_EFFECT];

    t_fm1_poly_voice data[FM1_POLYPHONY];
    t_voc_voices voices;

    long sampleNo;

    SGFLT fs;
    t_fm1_mono_modules mono_modules;

    SGFLT sv_last_note;  //For glide
    SGFLT sv_pitch_bend_value;
    t_plugin_event_queue midi_queue;
    SGFLT port_table[FM1_COUNT];
    t_plugin_event_queue atm_queue;
    t_plugin_cc_map cc_map;
    PluginDescriptor * descriptor;
    char pad2[CACHE_LINE_SIZE];
} t_fm1;

void g_fm1_poly_init(
    t_fm1_poly_voice* voice,
    SGFLT a_sr,
    t_fm1_mono_modules* a_mono,
    int voice_num
);

void v_fm1_poly_note_off(t_fm1_poly_voice * a_voice, int a_fast);

void v_fm1_mono_init(t_fm1_mono_modules*, SGFLT);
PluginDescriptor *fm1_plugin_descriptor();

#endif /* FM1_PLUGIN_H */

