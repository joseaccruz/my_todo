from .report import Report
from .tasks import Task
from .utils import multisort, get_date_relative
from .config import *

TSK_TYPE_TEXT = {
    Task.TASK_TYPE_DONE: "DONE",
    Task.TASK_TYPE_READY: "READY",
    Task.TASK_TYPE_WAITING: "WAITING"
}


def get_task_list(task):
    ret = {}

    if task._sc_type != Task.TASK_TYPE_DONE and task.is_leaf:
        tt = {}
        tt['task'] = task
        tt['index'] = task._index
        tt['type'] = task._sc_type

        tt['priority'] = task._sc_priority
        tt['start'] = task._sc_start
        tt['is_hard'] = task._sc_is_hard
        tt['due'] = task._sc_due
     
        tt['effort'] = task._sc_effort_minutes


        tt['is_recurrent'] = task._sc_is_recurrent
        tt['rec_type'] = task._sl_rec_type
        tt['rec_interval'] = task._sl_rec_interval
        tt['rec_period'] = task._sl_rec_period

        # look for the next WAITING sibling
        next_sibling = task._sc_next_sibling
        if (next_sibling is not None) and (next_sibling._sc_type == Task.TASK_TYPE_WAITING):
            tt['_next_sibling_index'] = next_sibling._index
        else:
            tt['_next_sibling_index'] = None

        ret[task._index] = tt

    for tchild in task._children:
        ret |= get_task_list(tchild)

    return ret


def sort_tasks(tasks, date):
    tsk = tasks.keys()
    tsk = list(filter(lambda k: tasks[k]['type'] == Task.TASK_TYPE_READY, tsk))
    tsk = list(filter(lambda k: tasks[k]['start'] <= date, tsk))
    tsk = sorted(tsk, key=lambda k: tasks[k]['due'])
    tsk = sorted(tsk, key=lambda k: tasks[k]['priority'], reverse=True)
    tsk = sorted(tsk, key=lambda k: tasks[k]['is_hard'], reverse=True)

    return tsk

MAX_HOURS_DAY = int(20 * 60)
MAX_SLOT_DUR = 3 * 60

def compute_free_time(plan):
    if len(plan) == 0:
        return MAX_HOURS_DAY
    else:
        return MAX_HOURS_DAY - sum([slot['effort'] for slot in plan])

def execute_task(tasks, tk, effort, date):
    #if (tasks[tk]['due'] < LAST_DUE):
    #    delta = (tasks[tk]['due'] - date).days
    #    if delta < 0:


    if tasks[tk]['effort'] > effort:
        # here we only remove some time to the task
        tasks[tk]['effort'] -= effort
        tasks[tk]['start'] = get_date_relative(date, 1, "d")
    else:
        # if the task has a dependent sibling mark it as READY
        next_sibling = tasks[tk]['_next_sibling_index']

        if next_sibling is not None:
            tasks[next_sibling]['type'] = Task.TASK_TYPE_READY

        # if the task is recurrent reschedule it
        if tasks[tk]['is_recurrent']:
            if tasks[tk]['rec_type'] == "in":
                tasks[tk]['start'] = get_date_relative(date, int(tasks[tk]['rec_interval']), tasks[tk]['rec_period'])
                # for now - we should recompute for the cases were the recurrent task is not executed in the day
                tasks[tk]['due'] = tasks[tk]['start'] 
            elif tasks[tk]['rec_type'] == "every":
                tasks[tk]['start'] = get_date_relative(tasks[tk]['start'], int(tasks[tk]['rec_interval']), tasks[tk]['rec_period'])
                tasks[tk]['due'] = tasks[tk]['start'] 
        else:
            # otherwise mark the task as done
            tasks[tk]['type'] = Task.TASK_TYPE_DONE

    return tasks

def place_task(tasks, free_time, tsk, date):
    for tk in tsk:
        effort = min(MAX_SLOT_DUR, tasks[tk]['effort'])

        if effort <= free_time:
            tasks = execute_task(tasks, tk, effort, date)

            return tk, effort, tasks

    return None, 0, tasks


def plan_day(date, tasks):
    plan = []

    while True:
        free_time = compute_free_time(plan)
        tsk = sort_tasks(tasks, date)

        tk, effort, tasks = place_task(tasks, free_time, tsk, date)

        if tk is None:
            # end of day for now
            break
        else:
            plan.append({'effort': effort, 'tk': tk})

    return plan, tasks


def show_calendar(calendar, tasks):
    for day in calendar:
        print()
        print(day['date'], day['count'])
        for slot in day['plan']:
            #print(tasks[slot['tk']])
            Report.show_task(tasks[slot['tk']]['task'].as_dict())

def simulate(task_root, start_date):
    tasks = get_task_list(task_root)

    calendar = []
    date = start_date

    for i in range(50):
        # stop when only recurrent tasks left
        
        tasks_tmp = list(filter(lambda k: not tasks[k]['is_recurrent'], sort_tasks(tasks, date)))
        count = len(tasks_tmp)

        if count > 0:
            plan, tasks = plan_day(date, tasks)
            calendar.append({'date': date, 'count': count, 'plan': plan})

            date = get_date_relative(date, 1, "d")

        else:
            break

    show_calendar(calendar, tasks)