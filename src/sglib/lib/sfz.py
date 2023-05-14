from .util import (
    AUDIO_FILE_EXTS,
    is_audio_file,
    read_file_text,
    string_to_note_num,
)
from sglib.lib import util
from sglib.log import LOG
import os
import re


class sfz_exception(Exception):
    pass

class sfz_sample:
    """ Corresponds to the settings for a single sample """
    def __init__(self):
        self.dict = {}

    def set_from_group(self, a_group_list):
        """ a_group_list: should be in order of least precedence to
        most precedence, ie:  values in the last group can overwrite
        values set by the first group."""
        for f_group in filter(None, a_group_list):
            for k, v in f_group.dict.items():
                if k not in self.dict or v is not None:
                    self.dict[k] = v

    def __str__(self):
        return str(self.dict)

def sfz_file_loader(
    path: str,
    defines: dict=None,
) -> list:
    """ Load an SFZ file by substituting all of the #definee's and recursively
        inserting all of the #include's

        @return:
            The individual, sanitized lines of the SFZ and every file that
            it references
    """
    defines = defines if defines else {}
    result = []
    try:
        with open(path) as f:
            text = f.read()
    except:
        LOG.exception(f"Failed to read SFZ file: {path}, trying utf-8")
        text = util.read_file_text(path)
    # Remove multiline comments
    text = re.sub(r"(\/\*.*\*\/)", ' ', text)
    text = re.sub(r"(\/\*.*\*\/)", '\n', text, flags=re.S)

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('//'):
            continue
        if '//' in line:
            line = line.split('//')[0]
        # Reverse the list to avoid the corner case of:
        # #define STRING abc
        # #define STRING_LONGER xyz
        for k in sorted(defines, reverse=True):
            v = defines[k]
            line = line.replace(k, v)

        if line.startswith("#define"):
            define = re.match(
                r'#define\s+(\$.*)\s+(.*)',
                line,
            )
            if not define:
                LOG.warning(f"Invalid #define '{define}'")
                continue
            defines[define.group(1)] = define.group(2)
        elif line.startswith('#include'):
            match = re.match(
                r'#include\s+"(.*)"',
                line,
            )
            _include = os.path.join(
                os.path.dirname(path),
                match.group(1),
            )
            inc_lines = sfz_file_loader(_include, defines)
            result.extend(inc_lines)
        else:
            result.append(line)

    return result

class sfz_file:
    """ Abstracts an .sfz file into a list of sfz_sample whose dicts
    correspond to the attributes of a single sample."""
    def __init__(self, a_file_path):
        self.path = str(a_file_path)
        if not os.path.exists(self.path):
            raise sfz_exception("{} does not exist.".format(self.path))
        f_file_text = "\n".join(sfz_file_loader(self.path))
        print(f_file_text)
        # In the wild, people can and often do put tags and opcodes on the same
        # line, move all tags and opcodes to their own line
        f_file_text = f_file_text.replace("<", "\n<")
        f_file_text = f_file_text.replace(">", ">\n")
        f_file_text = f_file_text.replace("\t", " ")
        f_file_text = f_file_text.replace("\r", "")

        f_file_text_new = ""

        for f_line in f_file_text.split("\n"):
            if "=" in f_line:
                f_line_arr = f_line.split("=")
                for f_i in range(1, len(f_line_arr)):
                    f_opcode = f_line_arr[f_i - 1].strip().rsplit(" ")[-1]
                    if f_i == (len(f_line_arr) - 1):
                        f_value = f_line_arr[f_i]
                    else:
                        f_value = f_line_arr[f_i].strip().rsplit(" ", 1)[0]
                    f_file_text_new += "\n{}={}\n".format(f_opcode, f_value)
            else:
                f_file_text_new += "{}\n".format(f_line)

        f_file_text = f_file_text_new
        self.adjusted_file_text = f_file_text_new

        f_global_settings = None
        f_current_group = None
        f_current_sequence = None
        f_current_object = None
        control = {}

        self.samples = []
        f_samples_list = []

        #None = unsupported, 0 = global, 1 = sequence, 2 = group, 3 = region
        f_current_mode = None

        for f_line in f_file_text.split("\n"):
            f_line = f_line.strip()

            if f_line == "" or f_line.startswith("//"):
                continue
            if re.match("<(.*)>", f_line) is not None:
                if f_line.startswith("<global>"):
                    f_current_mode = 0
                    f_global_settings = sfz_sample()
                    f_current_object = f_global_settings
                elif f_line.startswith("<sequence>"):
                    f_current_mode = 1
                    f_current_sequence = sfz_sample()
                    f_current_object = f_current_sequence
                    f_samples_list.append(f_current_sequence)
                elif f_line.startswith("<group>"):
                    f_current_mode = 2
                    f_current_group = sfz_sample()
                    f_current_object = f_current_group
                elif f_line.startswith("<region>"):
                    f_current_mode = 3
                    f_current_object = sfz_sample()
                    f_samples_list.append(f_current_object)
                elif f_line.startswith("<control>"):
                    f_current_mode = 4
                    continue
                else:
                    f_current_mode = None
            else:
                if f_current_mode is None:
                    continue
                if f_current_mode == 4:
                    f_key, f_value = f_line.split("=", 1)
                    control[f_key.strip()] = f_value.strip()
                    continue
                try:
                    f_key, f_value = f_line.split("=")
                    f_value = string_to_note_num(f_value)
                except Exception as ex:
                    LOG.warning(
                        f"Error parsing key/value pair  {f_line}: {ex}",
                    )
                    continue
                if f_key.lower() == "sample":
                    if not is_audio_file(f_value.strip()):
                        LOG.error(
                            f"{f_value} not supported, only {AUDIO_FILE_EXTS} "
                            "supported."
                        )
                        continue
                    if 'default_path' in control:
                        f_value = os.path.join(
                            control['default_path'],
                            f_value,
                        )

                f_current_object.dict[f_key.lower()] = f_value
                if f_current_mode == 1:
                    f_current_object.set_from_group(
                        [f_global_settings, f_current_group],
                    )

        for f_sequence in f_samples_list:
            if "sample" in f_sequence.dict:
                self.samples.append(f_sequence)

    def __str__(self):
        #return self.adjusted_file_text
        f_result = ""
        for f_sample in self.samples:
            f_result += "\n\n{}\n\n".format(f_sample)
        return f_result

