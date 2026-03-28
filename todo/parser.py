import os
import re

from .tasks import Task
from .utils import *
from .config import *

# Line Token Types
LINE_TOKEN_EMPTY   = "LINE_EMPTY"
LINE_TOKEN_COMMENT = "LINE_COMMENT"
LINE_TOKEN_TASK    = "LINE_TASK"
LINE_TOKEN_OTHER   = "LINE_OTHER"


RE_DATE     = r"\d\d\d\d-\d\d-\d\d"

RE_DATE     = r"\d\d\d\d-\d\d-\d\d"
RE_INDENT = rf"(?P<indent>[ \t]*)"
RE_DONE   = rf"(?P<done>OK *\- *{RE_DATE} *\- *)"
RE_REC    = rf"\(rec (?P<rec_type>every|in) (?P<rec_interval>\d+)(?P<rec_period>[dwmy])\)"
RE_TASK   = rf"(?P<signal>[\!\*\^])/ *(?P<title>[^\.\:]+?) *({RE_REC})? *([\.\:])"
RE_PRIORITY = rf" +(?P<priority>\d)"
RE_EFFORT   = rf" +(?P<effort_value>\d+)(?P<effort_unit>[mhd])"
RE_START    = rf" +>(?P<start>{RE_DATE})"
RE_DUE      = rf" +(<(?P<due_abs>{RE_DATE})|(?P<due_rel_value>\+\d+)(?P<due_rel_unit>[dwm]))"

# Line token syntax patterns
LINE_TOKEN_PATTERNS = [
    (LINE_TOKEN_EMPTY,   r"^(#.*|[ \t]*)$"),
    (LINE_TOKEN_COMMENT, rf'^{RE_INDENT}(""")$'),
    (LINE_TOKEN_TASK,    rf"^{RE_INDENT}{RE_DONE}?{RE_TASK}({RE_PRIORITY}|{RE_START}|{RE_DUE}|{RE_EFFORT})*$"),
    (LINE_TOKEN_OTHER,   r".*")
]


class LineToken:
    def __init__(self, file_name, subject, line_num, line_raw, line_type, **kwargs):
        self._file_name = file_name
        self._subject = subject
        self._line_num = line_num
        self._line_raw = line_raw
        self._line_type = line_type
        self._info = kwargs

    def is_empty(self):
        return self._line_type == LINE_TOKEN_EMPTY

    def is_comment(self):
        return self._line_type == LINE_TOKEN_COMMENT

    def is_task(self):
        return self._line_type == LINE_TOKEN_TASK

    def is_other(self):
        return self._line_type == LINE_TOKEN_OTHER


class LineTokenFactory:
    def __init__(self, file_name, subject):
        self._file_name = file_name
        self._subject = subject

    def parse(self, line_num, line_raw):
        for (line_type, line_pattern) in LINE_TOKEN_PATTERNS:
            m = re.match(line_pattern, line_raw)

            if m is not None:
                return LineToken(self._file_name, self._subject, line_num, line_raw, line_type, **m.groupdict())

        assert False, "Pattern not found!\nFile: '{self._file_name}':{line_num}\n'{line_raw}'"  # pragma: no cover

class Parser:
    def __init__(self):
        self.reset()

    def reset(self):
        self._line_tokens = []

    def parse_raw_file(self, file_name):
        subject = os.path.splitext(os.path.basename(file_name))[0]

        ltf = LineTokenFactory(file_name, subject)

        for i, line_raw in enumerate(open(file_name)):
           self._line_tokens.append(ltf.parse(i + 1, line_raw.rstrip()))

        return self

    def parse_raw_path(self, path):
        if os.path.isfile(path):
            self.parse_raw_file(path)

        else:
            for (cur_path, _, file_names) in os.walk(path):
                for file_name in file_names:
                    if file_name.endswith(TODO_FILE_EXT):
                        self.parse_raw_file(os.path.join(cur_path, file_name))

    def parse_tokens(self):
        PARSE_STATE_OUTSIDE_COMMENTS = "OUTSIDE COMMENTS"
        PARSE_STATE_INSIDE_COMMENTS  = "INSIDE COMMENTS"

        parse_status = PARSE_STATE_OUTSIDE_COMMENTS

        task_root = Task()
        task_current = None

        for line_token in self._line_tokens:
            if line_token.is_empty():
                continue

            if parse_status == PARSE_STATE_OUTSIDE_COMMENTS:
                if line_token.is_comment():
                    parse_status = PARSE_STATE_INSIDE_COMMENTS

                elif line_token.is_task():
                    task = Task(line_token._subject, line_token._line_num, **line_token._info)

                    while (task_current is not None) and (task_current.indent >= task.indent):
                        task_current = task_current.parent

                    if task_current is None:
                        task_root.add_child(task)
                    else:
                        task_current.add_child(task)
                    
                    task_current = task

                elif line_token.is_other():
                    raise ParseError(line_token._subject, line_token._line_num, "Invalid task")
                    
                else:
                    assert False, f"Unexpecetd line token type: {line_token}" # pragma: no cover

            elif parse_status == PARSE_STATE_INSIDE_COMMENTS:
                if line_token.is_comment():
                    parse_status = PARSE_STATE_OUTSIDE_COMMENTS

                elif line_token.is_task():
                    raise ParseError(line_token._subject, line_token._line_num, "Task found inside comments")

                elif line_token.is_other():
                    pass

                else:
                    assert False, f"Unexpecetd line token type: {line_token}" # pragma: no cover

            else:
                assert False, "Unexpecetd parse_status: {parse_status}" # pragma: no cover

        return task_root


    def parse(self, path, holidays):
        self.parse_raw_path(path)

        # second pass: parse all tokens to build the task tree and returns the root
        return self.parse_tokens().build(holidays)


def parse_holidays(fname):
    return list(map(get_date, open(fname).read().strip().split("\n")))

def load_holidays(fname, today):
    def count_year(holidays, year):
        return len(list(filter(lambda d: d.year == year, holidays)))

    if not os.path.isfile(fname):
        holidays = []
    else:
        holidays = parse_holidays(fname)

    if len(holidays) == 0:
        print("No holidays available.")
    else:
        for y in [0, 1]:
            if count_year(holidays, today.year + y) == 0:
                print(f"No holidays for {today.year + y} available.")

    return holidays
