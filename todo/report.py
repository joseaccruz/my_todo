from .tasks import Task
from .utils import multisort

from .config import *

TASK_STATE_TEXT = {
    Task.TASK_STATE_DONE     : "DONE",
    Task.TASK_STATE_WAITING  : "WAITING",
    Task.TASK_STATE_NO_ACTION: "NO_ACTION",
    Task.TASK_STATE_ACTIVE   : "ACTIVE",
    Task.TASK_STATE_CRITICAL : "CRITICAL",
    Task.TASK_STATE_OVERDUE  : "OVERDUE !",
    Task.TASK_STATE_NOW      : "NOW !!"
}

TASK_PRIORITY_TEXT = [8595, 126, 8593, 9733]


class Report:

    def __init__(self, path, today, task_root, filters, sort_keys):
        assert task_root.is_root, "`TaskList` must be initialized with a 'root' task."

        # get info vars
        self._path = path
        self._today = today

        # get the full list of tasks
        self._tasks = task_root.get_list()

        # obtain and filter the list of task dictionaries
        self._tasks_dict = []

        for task in self._tasks:
            task_dict = task.as_dict()

            for k, v in filters.items():
                # test if the task complies with all filters and skip if not
                if isinstance(v, set) or isinstance(v, list):
                    if task_dict[k] not in v:
                        break
                elif task_dict[k] != v:
                    break
            else:
                self._tasks_dict.append(task_dict)

        # sort the list of dicts
        self._tasks_dict = multisort(self._tasks_dict, sort_keys)


    @staticmethod
    def report_header(path, date):
        hlines = [
            "-" * 60,
            f"Task list path: '{path}'",
            f"Current date:   '{date}'",
            "-" * 60
        ]

        return "\n".join(hlines)


    @staticmethod
    def report_date(date):
        if date in (FIRST_START, LAST_DUE):
            return "    --    "
        else:
            return date

    @staticmethod
    def report_signal(td):
        if td['signal'] == "!":
            return "!"
        else:
            return " "

    @staticmethod
    def report_priority(td):
        return f"{chr(TASK_PRIORITY_TEXT[td['priority']])}"

    @staticmethod
    def report_effort(td):
        txt = f"{td['effort_value']:>2s}{td['effort_unit']}" if td['effort_days'] > 0 else "   "
        txt += f" ({td['effort_density']:4.1f})"

        return f"{txt:>3s}"

    @staticmethod
    def report_state(td):
        return f"{TASK_STATE_TEXT[td['state']]:9s}"

    @staticmethod
    def report_subject(td, report_max_subject):
        txt = f"{td['subject']} ({td['line_num']})"

        return f"{txt:{report_max_subject + 7}s}"

    @staticmethod
    def report_path(td):
        return " < ".join(td['path'][::-1])

    @staticmethod
    def report_recurrent(td):
        if td['is_recurrent']:
            return f"(rec {td['rec_type']} {td['rec_interval']} {td['rec_period']})"
        else:
            return ""

    @staticmethod
    def show_task(td, max_subject_length=32):
        print(">>>>", end=" ")
        print(Report.report_date(td['start']), end=" -> ")
        print(Report.report_signal(td), end=" ")
        print(Report.report_date(td['due']), end=" ")
        print(Report.report_effort(td), end=" / ")

        print(Report.report_state(td), end=" | ")
        print(Report.report_subject(td, max_subject_length), end=" > ")
        
        print(Report.report_priority(td), end=" - ")
        print(Report.report_path(td), end=" ")
        print(Report.report_recurrent(td))

    def display_terminal(self, num):
        num = len(self._tasks_dict) if num == 0 else num

        if len(self._tasks_dict) == 0:
            print("Task list is empty.")
        else:
            max_subject_length = max(map(lambda td: len(td['subject']), self._tasks_dict))

            print(self.report_header(self._path, self._today), end="\n\n")
                
            for td in self._tasks_dict[:num]:
                self.show_task(td, max_subject_length)

            print(f" \n\t{len(self._tasks_dict)} tasks found. {num} tasks shown.")

    def display_test(self):
        if len(self._tasks) == 0:
            print("-")
        else:
            txt = map(str, self._tasks)

            print("\n".join(sorted(txt)))