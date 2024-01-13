#ifdef NO_MIDI
    #include <portmidi.h>
#endif
#include <string.h>
#include <sys/time.h>
#include <time.h>

#include "compiler.h"
#include "files.h"
#include "hardware/config.h"
#include "hardware/midi.h"

#ifdef NO_MIDI
    void midiPoll(void * arg){}
    void midiDeviceRead(void* arg1, SGFLT arg2, unsigned long arg3){}
    void open_midi_devices(
        struct HardwareConfig* config
    ){}
    void close_midi_devices(){}
    NO_OPTIMIZATION int midiDeviceInit(
        t_midi_device * self,
        char * f_midi_device_name
    );

#else

NO_OPTIMIZATION void open_midi_devices(
    struct HardwareConfig* config
){
    int i;
    f_midi_err = Pm_Initialize();
    MIDI_DEVICES.count = 0;

    char* f_midi_device_name;
    for(i = 0; i < config->midi_in_device_count; ++i){
        f_midi_device_name = config->midi_in_device_names[i];
        int f_device_result = midiDeviceInit(
            &MIDI_DEVICES.devices[MIDI_DEVICES.count],
            f_midi_device_name
        );

        if(f_device_result == 0){
            log_info(
                "Initialized MIDI device %i '%s' as device %i",
                i,
                f_midi_device_name,
                MIDI_DEVICES.count
            );
        } else if(f_device_result == 1){
            log_error(
                "Did not find MIDI device '%s'",
                f_midi_device_name
            );
            /*++f_failure_count;
            sprintf(f_cmd_buffer, "%s \"%s %s\"", f_show_dialog_cmd,
                "Error: did not find MIDI device:",
                f_midi_device_name);
            system(f_cmd_buffer);
            continue;*/
        } else if(f_device_result == 2){
            log_error(
                "Could not open MIDI device '%s'",
                f_midi_device_name
            );
            /*++f_failure_count;
            sprintf(f_cmd_buffer, "%s \"%s %s, %s\"",
                f_show_dialog_cmd, "Error opening MIDI device: ",
                f_midi_device_name, Pm_GetErrorText(f_midi_err));
            system(f_cmd_buffer);
            continue;*/
        }

        ++MIDI_DEVICES.count;
    }
}

NO_OPTIMIZATION void close_midi_devices(){
    int i;
    for(i = 0; i < MIDI_DEVICES.count; ++i){
        if(MIDI_DEVICES.devices[i].loaded){
            midiDeviceClose(&MIDI_DEVICES.devices[i]);
        }
    }
    Pm_Terminate();
}

NO_OPTIMIZATION int midiDeviceInit(
    t_midi_device * self,
    char * f_midi_device_name
){
    self->instanceEventCounts = 0;
    self->midiEventReadIndex = 0;
    self->midiEventWriteIndex = 0;
    self->loaded = 0;
    self->f_device_id = pmNoDevice;
    self->name[0] = '\0';
    sg_snprintf(self->name, 256, "%s", f_midi_device_name);
    char device_name[1024] = {};
    int j;
    char* pm_name;

    if(strcmp(f_midi_device_name, "None"))
    {
        int f_i;
        int f_count = Pm_CountDevices();

        for(f_i = 0; f_i < f_count; ++f_i){
            const PmDeviceInfo * f_device = Pm_GetDeviceInfo(f_i);
            j = 0;
            pm_name = (char*)f_device->name;
            // Replace pipe characters, which would cause issues parsing
            // the config file.  The UI also replaces pipe characters when
            // creating the file
            while(1){
                if(*pm_name != '|'){
                    device_name[j] = *pm_name;
                    ++j;
                }
                if(*pm_name == '\0' || j >= 1000){
                    break;
                }
                ++pm_name;
            }
            if(f_device->input && !strcmp(device_name, f_midi_device_name)){
                self->f_device_id = f_i;
                break;
            }
        }

        if(self->f_device_id == pmNoDevice){
            return 1;
        }

        log_info("Opening MIDI device ID: %i", self->f_device_id);
        self->f_midi_err = Pm_OpenInput(
            &self->f_midi_stream,
            self->f_device_id,
            NULL,
            MIDI_EVENT_BUFFER_SIZE,
            NULL,
            NULL
        );

        if(self->f_midi_err != pmNoError){
            return 2;
        }
    }

    self->loaded = 1;

    return 0;
}

NO_OPTIMIZATION void midiDeviceClose(t_midi_device * self){
    Pm_Close(self->f_midi_stream);
}

void midi_device_inc_writer(
    t_midi_device * self
){
    /* At this point we change the event timestamp so that its
   real-time field contains the actual time at which it was
   received and processed (i.e. now).  Then in the audio
   callback we use that to calculate frame offset. */

    struct timeval tv;
    t_seq_event* event = &self->midiEventBuffer[self->midiEventWriteIndex];

    gettimeofday(&tv, NULL);
    event->tv_sec = tv.tv_sec;
    event->tv_nsec = tv.tv_usec * 1000L;

    ++self->midiEventWriteIndex;

    if(self->midiEventWriteIndex >= MIDI_EVENT_BUFFER_SIZE){
        self->midiEventWriteIndex = 0;
    }
}

void midiReceive(
    t_midi_device * self,
    unsigned char status,
    unsigned char control,
    char value,
    int _channel
){
    unsigned char channel;
    if(_channel == 17){
        channel = status & 0x0F;
    } else {
        channel = _channel;
    }
    unsigned char opCode = status & 0xF0;
    if (opCode >= 0xF0)
    {
        opCode = status;
    }

    //int twoBytes = 1;

    if(self->midiEventReadIndex == self->midiEventWriteIndex + 1)
    {
        log_warn("MIDI event buffer overflow, ignoring incoming event");
        return;
    }

    switch (opCode)
    {
        case MIDI_PITCH_BEND:
        {
            //twoBytes = 0;
            int f_pb_val = ((value << 7) | control) - 8192;
            v_ev_set_pitchbend(
                &self->midiEventBuffer[self->midiEventWriteIndex],
                channel,
                f_pb_val
            );
            midi_device_inc_writer(self);
            //log_info("MIDI PITCHBEND status %i ch %i, value %i",
            //      status, channel+1, f_pb_val);
        }
            break;
        case MIDI_NOTE_OFF:
            v_ev_set_noteoff(
                &self->midiEventBuffer[self->midiEventWriteIndex],
                channel,
                control,
                value
            );
            midi_device_inc_writer(self);
            /*log_info(
             * "MIDI NOTE_OFF status %i (ch %i, opcode %i), ctrl %i, val %i",
             * status, channel+1, (status & 255)>>4, control, value);*/
            break;
        case MIDI_NOTE_ON:
            if(value == 0){
                v_ev_set_noteoff(
                    &self->midiEventBuffer[self->midiEventWriteIndex],
                    channel,
                    control,
                    value
                );
            } else {
                v_ev_set_noteon(
                    &self->midiEventBuffer[self->midiEventWriteIndex],
                    channel,
                    control,
                    value,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0
                );
            }
            midi_device_inc_writer(self);
            /*log_info("MIDI NOTE_ON status %i (ch %i, opcode %i), ctrl %i, "
                    "val %i\n", status, channel+1, (status & 255)>>4, control,
                    value);*/
            break;
        //case MIDI_AFTERTOUCH:
        case MIDI_CC:
            v_ev_set_controller(
                &self->midiEventBuffer[self->midiEventWriteIndex],
                channel,
                control,
                value
            );
            midi_device_inc_writer(self);
            /*log_info("MIDI CC status %i (ch %i, opcode %i), ctrl %i, "
                    "val %i\n", status, channel+1, (status & 255)>>4, control,
                    value);*/
            break;
        default:
            //twoBytes = 0;
            /*message = QString("MIDI status 0x%1")
                 .arg(QString::number(status, 16).toUpper());*/
            break;
    }

}

void midiPoll(t_midi_device * self){
    PmError f_poll_result;
    int f_bInSysex = 0;
    unsigned char status;
    //int f_cReceiveMsg_index = 0;
    int i;
    int channel;
    if(!self->route){
        channel = 0;
    } else {
        channel = self->route->channel;
    }

    f_poll_result = Pm_Poll(self->f_midi_stream);
    if(f_poll_result < 0){
        log_info("Portmidi error %s", Pm_GetErrorText(f_poll_result));
    } else if(f_poll_result > 0){
        int numEvents = Pm_Read(
            self->f_midi_stream,
            self->portMidiBuffer,
            MIDI_EVENT_BUFFER_SIZE
        );

        if (numEvents < 0){
            log_info("PortMidi error: %s", Pm_GetErrorText((PmError)numEvents));
        } else if(numEvents > 0){
            for (i = 0; i < numEvents; i++){
                status = Pm_MessageStatus(self->portMidiBuffer[i].message);

                if ((status & 0xF8) == 0xF8) {
                    // Handle real-time MIDI messages at any time
                    midiReceive(self, status, 0, 0, channel);
                }

                reprocessMessage:

                if (!f_bInSysex){
                    if (status == 0xF0) {
                        f_bInSysex = 1;
                        status = 0;
                    } else {
                        //unsigned char channel = status & 0x0F;
                        unsigned char note = Pm_MessageData1(
                            self->portMidiBuffer[i].message
                        );
                        unsigned char velocity = Pm_MessageData2(
                            self->portMidiBuffer[i].message
                        );
                        midiReceive(self, status, note, velocity, channel);
                    }
                }

                if(f_bInSysex){
                    // Abort (drop) the current System Exclusive message if a
                    // non-realtime status byte was received
                    if (status > 0x7F && status < 0xF7){
                        f_bInSysex = 0;
                        //f_cReceiveMsg_index = 0;
                        log_info("Buggy MIDI device: SysEx interrupted");
                        goto reprocessMessage;  // Don't lose the new message
                    }

                    // Collect bytes from PmMessage
                    int data = 0;
                    int shift;
                    for(
                        shift = 0;
                        shift < 32 && (data != MIDI_EOX);
                        shift += 8
                    ){
                        if ((data & 0xF8) == 0xF8){
                            // Handle real-time messages at any time
                            midiReceive(self, data, 0, 0, channel);
                        } else {
                            //m_cReceiveMsg[m_cReceiveMsg_index++] = data =
                            //    (portMidiBuffer[i].message >> shift) & 0xFF;
                        }
                    }

                    // End System Exclusive message if the EOX byte was received
                    if (data == MIDI_EOX){
                        f_bInSysex = 0;
                        log_info(
                            "Dropping MIDI message in if (data == MIDI_EOX)"
                        );
                        //const char* buffer =
                                //reinterpret_cast<const char*>(m_cReceiveMsg);
                        //receive(QByteArray::fromRawData(buffer,
                        //        m_cReceiveMsg_index));
                        //f_cReceiveMsg_index = 0;
                    } //if (data == MIDI_EOX)
                } //if(f_bInSysex)
            } //for (i = 0; i < numEvents; i++)
        } //else if(numEvents > 0)
    } //else if(f_poll_result > 0)
}

void midiDeviceRead(
    t_midi_device* self,
    SGFLT sample_rate,
    unsigned long framesPerBuffer
){
    struct timeval tv, evtv, diff;
    long framediff;
    double dframediff;

    gettimeofday(&tv, NULL);

    self->instanceEventCounts = 0;

    while(self->midiEventReadIndex != self->midiEventWriteIndex){
        t_seq_event *ev =
            &self->midiEventBuffer[self->midiEventReadIndex];

        /*
        if (!v_ev_is_channel_type(ev))
        {
            midiEventReadIndex++
            //discard non-channel oriented messages
            continue;
        }
        */

        /* Stop processing incoming MIDI if an instance's event buffer is
         * full. */
        if (self->instanceEventCounts == MIDI_EVENT_BUFFER_SIZE){
            break;
        }

        /* Each event has a real-time timestamp indicating when it was
         * received (set by midi_callback).  We need to calculate the
         * difference between then and the start of the audio callback
         * (held in tv), and use that to assign a frame offset, to
         * avoid jitter.  We should stop processing when we reach any
         * event received after the start of the audio callback. */

        evtv.tv_sec = ev->tv_sec;
        evtv.tv_usec = ev->tv_nsec / 1000;

        if (
            evtv.tv_sec > tv.tv_sec
            ||
            (evtv.tv_sec == tv.tv_sec && evtv.tv_usec > tv.tv_usec)
        ){
            break;
        }

        diff.tv_sec = tv.tv_sec - evtv.tv_sec;
        if (tv.tv_usec < evtv.tv_usec){
            --diff.tv_sec;
            diff.tv_usec = tv.tv_usec + 1000000 - evtv.tv_usec;
        } else {
            diff.tv_usec = tv.tv_usec - evtv.tv_usec;
        }

        dframediff = ((double)diff.tv_sec + (
            (double)diff.tv_usec * 0.000001
        )) * sample_rate;
        framediff = (long)dframediff;

        if (framediff >= framesPerBuffer){
            framediff = framesPerBuffer - 1;
        } else if (framediff < 0){
            framediff = 0;
        }

        ev->tick = framesPerBuffer - framediff - 1;
        int f_max_tick = framesPerBuffer - 1;

        if(ev->tick < 0){
            ev->tick = 0;
        } else if(ev->tick > f_max_tick){
            ev->tick = f_max_tick;
        }

        if (ev->type == EVENT_CONTROLLER){
            int controller = ev->param;

            if (controller == 0){
                // bank select MSB
            } else if (controller == 32){
                // bank select LSB
            } else if (controller > 0 && controller < MIDI_CONTROLLER_COUNT){
                self->instanceEventBuffers[self->instanceEventCounts] = *ev;
                ++self->instanceEventCounts;
            } else {
                sg_abort("midiDeviceRead: Unknown controller: %i", controller);
            }
        } else {
            self->instanceEventBuffers[self->instanceEventCounts] = *ev;
            ++self->instanceEventCounts;
        }

        ++self->midiEventReadIndex;
        if(self->midiEventReadIndex >= MIDI_EVENT_BUFFER_SIZE){
            self->midiEventReadIndex = 0;
        }
    }

    sg_assert(
        self->instanceEventCounts < MIDI_EVENT_BUFFER_SIZE,
        "midiDeviceRead: instance event count out %i out of range 0 to %i",
        self->instanceEventCounts,
        MIDI_EVENT_BUFFER_SIZE
    );
}

#endif
