import datetime as dt


TODO_FILE_EXT = ".todo"

FIRST_START = dt.date(1900, 1, 1)
LAST_DUE = dt.date(2100, 12, 31)


MAX_HOURS_PER_DAY = 3

EFFORT_RATIO = {
    'm': 1,
    'h': 60,
    'd': 60 * MAX_HOURS_PER_DAY
}
