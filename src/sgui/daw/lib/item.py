from sglib import constants
from sglib.log import LOG
from sglib.math import clip_value
from sglib.models.daw.audio_item import DawAudioItem
from sglib.models.stargate.midi_events import cc, note, pitchbend
from sglib.models.daw.seq_item import sequencer_item
from sgui.daw import painter_path
import os
import shutil

def save_item_by_uid(
    a_uid,
    a_item,
    a_new_item=False,
):
    painter_path.pop_path_from_cache(a_uid)
    constants.DAW_PROJECT.save_item_by_uid(a_uid, a_item, a_new_item)

def save_item(a_name, a_item):
    project = constants.DAW_PROJECT
    if not project.suppress_updates:
        f_items_dict = project.get_items_dict()
        f_uid = f_items_dict.get_uid_by_name(a_name)
        assert f_uid == a_item.uid, "UIDs do not match"
        save_item_by_uid(f_uid, a_item)

def save_recorded_items(
    a_item_name,
    a_mrec_list,
    a_overdub,
    a_sr,
    a_start_beat,
    a_end_beat,
    a_audio_inputs,
    a_sample_count,
    a_file_name,
):
    LOG.info("\n".join(a_mrec_list))

    project = constants.DAW_PROJECT
    f_audio_files_dict = {}

    for f_i, f_ai in zip(range(len(a_audio_inputs)), a_audio_inputs):
        f_val = f_ai.get_value()
        if f_val.rec:
            f_path = os.path.join(
                constants.PROJECT.audio_tmp_folder, "{}.wav".format(f_i))
            if os.path.isfile(f_path):
                f_file_name = "-".join(
                    str(x) for x in (a_file_name, f_i, f_ai.get_name()))
                f_new_path = os.path.join(
                    constants.PROJECT.audio_rec_folder, f_file_name)
                if f_new_path.lower().endswith(".wav"):
                    f_new_path = f_new_path[:-4]
                if os.path.exists(f_new_path + ".wav"):
                    for f_i in range(10000):
                        f_tmp = "{}-{}.wav".format(f_new_path, f_i)
                        if not os.path.exists(f_tmp):
                            f_new_path = f_tmp
                            break
                else:
                    f_new_path += ".wav"
                shutil.move(f_path, f_new_path)
                f_uid = constants.PROJECT.get_wav_uid_by_name(f_new_path)
                sg = constants.PROJECT.get_sample_graph_by_uid(f_uid)

                f_audio_files_dict[f_i] = (
                    f_new_path,
                    f_uid,
                    sg.frame_count,
                    f_val.output,
                    f_val.sidechain,
                )
            else:
                LOG.error("Error, path did not exist: {}".format(f_path))

    f_audio_frame = 0

    f_mrec_items = [x.split("|") for x in a_mrec_list]
    f_mrec_items.sort(key=lambda x: int(x[-1]))
    LOG.info("\n".join(str(x) for x in f_mrec_items))
    f_item_length = a_end_beat - a_start_beat
    f_sequencer = project.get_sequence()
    f_note_tracker = {}
    f_items_to_save = {}
    project.rec_item = None
    f_item_name = str(a_item_name)
    f_items_dict = project.get_items_dict()
    f_orig_items = {}
    project.rec_take = {}

    f_audio_tracks = [x[3] for x in f_audio_files_dict.values()]
    f_midi_tracks = [int(x[2]) for x in f_mrec_items]
    f_active_tracks = set(f_audio_tracks + f_midi_tracks)

    f_sequencer.clear_range(f_active_tracks, a_start_beat, a_end_beat)

    def get_item(a_track_num):
        if a_track_num in f_orig_items:
            return f_orig_items[a_track_num].item_uid
        return None

    def new_take():
        project.rec_take = {}
        for f_track in f_active_tracks:
            copy_take(f_track)
        for k, v in f_audio_files_dict.items():
            f_path, f_uid, f_frames, f_output, f_mode = v
            f_item = project.rec_take[f_output]
            f_lane = f_item.get_next_lane()
            f_start = (f_audio_frame / f_frames) * 1000.0
            f_end = 1000.0
            #(f_audio_frame / (f_frames + a_sample_count)) * 1000.0
            f_start = clip_value(f_start, 0.0, f_end)
            f_end = clip_value(f_end, f_start, 1000.0)
            f_audio_item = DawAudioItem(
                f_uid, a_sample_start=f_start, a_sample_end=f_end,
                a_output_track=f_mode, a_lane_num=f_lane)
            f_index = f_item.get_next_index()
            f_item.add_item(f_index, f_audio_item)

    def copy_take(a_track_num):
        if a_overdub:
            copy_item(a_track_num)
        else:
            new_item(a_track_num)

    def new_item(a_track_num):
        f_name = project.get_next_default_item_name(f_item_name)
        f_uid = project.create_empty_item(f_name)
        f_item = project.get_item_by_uid(f_uid)
        f_items_to_save[f_uid] = f_item
        project.rec_take[a_track_num] = f_item
        f_item_ref = sequencer_item(
            a_track_num,
            a_start_beat,
            f_item_length,
            f_uid,
        )
        f_sequencer.add_item_ref_by_uid(f_item_ref)

    def copy_item(a_track_num):
        f_uid = get_item(a_track_num)
        if f_uid is not None:
            f_old_name = f_items_dict.get_name_by_uid(f_uid)
            f_name = project.get_next_default_item_name(
                f_item_name)
            f_uid = project.copy_item(f_old_name, f_name)
            f_item = project.get_item_by_uid(f_uid)
            f_items_to_save[f_uid] = f_item
            project.rec_take[a_track_num] = f_item
            f_item_ref = sequencer_item(
                a_track_num,
                a_start_beat,
                f_item_length,
                f_uid,
            )
            f_sequencer.add_item_ref_by_uid(f_item_ref)
        else:
            new_item(a_track_num)

    def set_note_length(a_track_num, f_note_num, f_end_beat, f_tick):
        f_note = f_note_tracker[a_track_num][f_note_num]
        f_length = f_end_beat - f_note.start
        if f_length > 0.0:
            f_note.set_length(f_length)
        else:
            assert False, "Need a different algorithm for this"
            LOG.info("Using tick length for:")
            f_sample_count = f_tick - f_note.start_sample
            f_seconds = float(f_sample_count) / float(a_sr)
            f_note.set_length(f_seconds * f_beats_per_second)
        LOG.info(f_note_tracker[a_track_num].pop(f_note_num))

    new_take()

    for f_event in f_mrec_items:
        f_type, f_beat, f_track = f_event[:3]
        f_track = int(f_track)
        f_beat = float(f_beat)
        if not f_track in f_note_tracker:
            f_note_tracker[f_track] = {}

        f_is_looping = f_type == "loop"

        if f_is_looping:
            new_take()

        if f_type == "loop":
            LOG.info("Loop event")
            f_audio_frame += a_sample_count
            continue

        project.rec_item = project.rec_take[f_track]

        if f_type == "on":
            f_note_num, f_velocity, f_tick = (int(x) for x in f_event[3:])
            LOG.info("New note: {} {}".format(f_beat, f_note_num))
            f_note = note(f_beat, 1.0, f_note_num, f_velocity)
            f_note.start_sample = f_tick
            if f_note_num in f_note_tracker[f_track]:
                LOG.info("Terminating note early: {}".format(
                    (f_track, f_note_num, f_tick)))
                set_note_length(
                    f_track, f_note_num, f_beat, f_tick)
            f_note_tracker[f_track][f_note_num] = f_note
            project.rec_item.add_note(f_note, a_check=False)
        elif f_type == "off":
            f_note_num, f_tick = (int(x) for x in f_event[3:])
            if f_note_num in f_note_tracker[f_track]:
                set_note_length(
                    f_track, f_note_num, f_beat, f_tick)
            else:
                LOG.error("Error:  note event not in note tracker")
        elif f_type == "cc":
            f_port, f_val, f_tick = f_event[3:]
            f_port = int(f_port)
            f_val = float(f_val)
            f_cc = cc(f_beat, f_port, f_val)
            project.rec_item.add_cc(f_cc)
        elif f_type == "pb":
            f_val = float(f_event[3]) / 8192.0
            f_val = clip_value(f_val, -1.0, 1.0)
            f_pb = pitchbend(f_beat, f_val)
            project.rec_item.add_pb(f_pb)
        else:
            LOG.error("Invalid mrec event type {}".format(f_type))

    for f_uid, f_item in f_items_to_save.items():
        f_item.fix_overlaps()
        save_item_by_uid(f_uid, f_item, a_new_item=True)

    project.save_sequence(f_sequencer)
    project.commit("Record")

