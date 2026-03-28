import datetime as dt
import re

from operator import itemgetter

from dateutil.relativedelta import relativedelta



class TodoError(Exception):
    def __init__(self, subject, line_num, message):
        super().__init__(f"'{subject}':{line_num}:{message}")

class LogicError(TodoError):
    pass

class ParseError(TodoError):
    pass

class ParameterError(Exception):
    pass

def multisort(items, keys):
    for key, ascending in reversed(keys):
        items.sort(key=itemgetter(key), reverse=not ascending)

    return items

def get_date(text):
    return dt.datetime.strptime(text, "%Y-%m-%d").date()

def add_business_days(date, n, holidays=[]):
    td = dt.timedelta(days=1)

    inc = -1 if n > 0 else 1

    while n != 0:
        if inc < 0:
            date += td
        else:
            date -= td

        n += inc if (date.weekday() <= 4) and (date not in holidays) else 0

    return date

def get_date_relative(date, value, unit, holidays=[]):
    assert unit in "dwm", f"Bad unit for relative date {unit}"   # pragma: no cover

    if unit == 'd':
        return add_business_days(date, value, holidays)
    else:
        date_unit = {'w': 'weeks', 'm': 'months'}[unit]
        return date + relativedelta(**{date_unit: value})
