import argparse
import os
import datetime as dt
import re

from todo.parser import Parser, load_holidays
from todo.report import Report
from todo.simul import simulate
from todo.tasks import Task
from todo.utils import get_date, get_date_relative, LogicError, ParseError, ParameterError

try:
    if __name__ == "__main__":
        parser = argparse.ArgumentParser()

        parser.add_argument('mode', nargs="?", default="mini", choices=['mini', 'all', 'simul'])
        parser.add_argument('-n', '--num', default=0)
        parser.add_argument('-p', '--path', default=".")
        parser.add_argument('-d', '--date', default=None)
        parser.add_argument('-f', '--holidays', default=None)
        parser.add_argument('-t', '--test', action="store_true")

        args = parser.parse_args()

        if args.mode == 'mini':
            filters = {'state': [Task.TASK_STATE_ACTIVE, Task.TASK_STATE_CRITICAL, Task.TASK_STATE_OVERDUE, Task.TASK_STATE_NOW]}
            sort_keys = [('state', False), ('effort_density', False), ('priority', False)]

        elif args.mode == 'all':
            filters = {'is_done': False}
            sort_keys = [('subject', True), ('line_num', True)]


        today = dt.datetime.today().date()
        
        if args.date:
            if re.match(r"\+\d+[dwm]", args.date):
                today = get_date_relative(today, int(args.date[:-1]), args.date[-1])

            elif re.match(r"\d\d\d\d\-\d\d-\d\d", args.date):
                today = get_date(args.date)

            else:    
                raise ParameterError("Argument 'Date' must be either a date 'Y-m-d' or a relative offset in the format: +nd, +nw, +nm")
     
        # load holidays
        holidays = load_holidays(args.holidays if args.holidays is not None else os.path.join(args.path, "holidays.csv"), today)

        # parse all files
        task_root = Parser().parse(args.path, holidays)

        task_root.compute_state_today(today, holidays)

        # display results
        if args.test:
            Report(args.path, today, task_root, filters, sort_keys).display_test()
        elif args.mode == 'simul':
            simulate(task_root, today)
        else:
            Report(args.path, today, task_root, filters, sort_keys).display_terminal(int(args.num))



except LogicError as e:
    print(f"Logic error detected in your TODO source:\n\t{e}")

except ParameterError as e:
    print(f"Invalid parameters calling `todo.py`:\n\t{e}")

except ParseError as e:
    print(f"Syntax error detected in your TODO source:\n\t{e}")
