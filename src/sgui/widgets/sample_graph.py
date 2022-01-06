from sglib import constants
from sglib.math import db_to_lin
from sgui.shared import (
    AUDIO_ITEM_SCENE_HEIGHT,
    AUDIO_ITEM_SCENE_WIDTH,
)
from sgui.sgqt import *

def create_sample_graph(
    sample_graph,
    a_for_scene=False,
    a_width=None,
    a_height=None,
    a_audio_item=None,
):
    if a_audio_item:
        f_ss = a_audio_item.sample_start * 0.001
        f_se = a_audio_item.sample_end * 0.001
        #f_width_frac = f_se - f_ss
        audio_pool = constants.PROJECT.get_audio_pool()
        by_uid = audio_pool.by_uid()
        ap_entry = by_uid[a_audio_item.uid]
        f_vol = db_to_lin(a_audio_item.vol + ap_entry.volume)
        f_len = len(sample_graph.high_peaks[0])
        f_slice_start = int(f_ss * f_len)
        f_slice_end = int(f_se * f_len)
        #a_width *= f_width_frac
    else:
        f_slice_start = None
        f_slice_end = None
    if a_width or a_height or sample_graph.cache is None:
        if not a_width:
            a_width = AUDIO_ITEM_SCENE_WIDTH
        if not a_height:
            a_height = AUDIO_ITEM_SCENE_HEIGHT

        if a_for_scene:
            f_width_inc = a_width / sample_graph.count
            f_section = a_height / float(sample_graph.channels)
        else:
            f_width_inc = 98.0 / sample_graph.count
            f_section = 100.0 / float(sample_graph.channels)
        f_section_div2 = f_section * 0.5

        f_paths = []

        for f_i in range(sample_graph.channels):
            f_result = QPainterPath()
            f_width_pos = 1.0
            f_result.moveTo(f_width_pos, f_section_div2)
            if a_audio_item and a_audio_item.reversed:
                f_high_peaks = sample_graph.high_peaks[f_i][
                    f_slice_end:f_slice_start:-1]
                f_low_peaks = sample_graph.low_peaks[f_i][::-1]
                f_low_peaks = f_low_peaks[f_slice_start:f_slice_end]
            else:
                f_high_peaks = sample_graph.high_peaks[f_i][
                    f_slice_start:f_slice_end]
                f_low_peaks = sample_graph.low_peaks[f_i][::-1]
                f_low_peaks = f_low_peaks[f_slice_end:f_slice_start:-1]

            if a_audio_item:
                f_high_peaks = f_high_peaks * f_vol
                f_low_peaks = f_low_peaks * f_vol

            for f_peak in f_high_peaks:
                f_result.lineTo(
                    f_width_pos,
                    f_section_div2 - (f_peak * f_section_div2),
                )
                f_width_pos += f_width_inc
            for f_peak in f_low_peaks:
                f_result.lineTo(
                    f_width_pos,
                    (f_peak * -1.0 * f_section_div2) + f_section_div2,
                )
                f_width_pos -= f_width_inc
            f_result.closeSubpath()
            f_paths.append(f_result)
        if a_width or a_height:
            return f_paths
        sample_graph.cache = f_paths
    return sample_graph.cache

