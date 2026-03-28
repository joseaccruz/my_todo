"""(If it does not have any child.)

ACTIVE? - If it's "*" or "!" and or's not done

HARD - It it's "!""
"""
import datetime as dt
import math

import numpy as np

from .utils import *
from .config import *

class Task:
    TASK_TYPE_DONE = 1
    TASK_TYPE_READY = 2
    TASK_TYPE_WAITING = 3

    TASK_STATE_DONE      = 0
    TASK_STATE_WAITING   = 1
    TASK_STATE_NO_ACTION = 2
    TASK_STATE_ACTIVE    = 3
    TASK_STATE_CRITICAL  = 4
    TASK_STATE_OVERDUE   = 5
    TASK_STATE_NOW       = 6

    def __init__(self, subject="ROOT", line_num=0, **kwargs):
        """
        Properties naming conventions:
            _<prop>    -> depend on the position of the task in the task tree.
            _f_<prop>  -> depend on the source file information.
            _sl_<prop> -> static / literal - depends on the parsed information only.
            _sc_<prop> -> static / computed - computed from the static/literal w.o. extra information
            _d_<prop>  -> dynamic - depends on the state of other tasks (parent, sibling, ...), on the date of reporting
        """

        # Task tree properties
        self._parent = None
        self._children = []

        # file properties
        self._f_subject = subject
        self._f_line_num = line_num

        """
        Static literal properties:
            - Do not depend on the current date
            - Are exatcly as read from the input file
        """
        self._sl_indent        = len(kwargs.get('indent', ""))
        self._sl_done          = kwargs.get('done')
        self._sl_signal        = kwargs.get('signal', "*")
        self._sl_title         = kwargs.get('title', "")
        self._sl_rec_type      = kwargs.get('rec_type')
        self._sl_rec_interval  = kwargs.get('rec_interval')
        self._sl_rec_period    = kwargs.get('rec_period')
        self._sl_priority      = kwargs.get('priority')
        self._sl_start         = kwargs.get('start')
        self._sl_due_abs       = kwargs.get('due_abs')
        self._sl_due_rel_value = kwargs.get('due_rel_value')
        self._sl_due_rel_unit  = kwargs.get('due_rel_unit')
        self._sl_effort_value  = kwargs.get('effort_value')
        self._sl_effort_unit   = kwargs.get('effort_unit')

        """
        Static computed properties:
            - Do not depend on the current date
            - Are computed as functions of status literal properties or their parents
        """
        if self._sl_done is not None:
            self._sc_type = self.TASK_TYPE_DONE
        elif self._sl_signal == "^":
            self._sc_type = self.TASK_TYPE_WAITING
        else:
            self._sc_type = self.TASK_TYPE_READY
        
        self._sc_is_hard = (self._sl_signal == "!")

        self._sc_is_recurrent = (not self._sl_rec_type is None)

        if self._sl_effort_value is None:
            self._sc_effort_minutes = 0
            self._sc_effort_days = 0
        else:
            # effort in minutes (4h / day)
            self._sc_effort_minutes = int(self._sl_effort_value) * EFFORT_RATIO[self._sl_effort_unit]

            # effort in days with a rate of 4h / day
            self._sc_effort_days = int(math.ceil(self._sc_effort_minutes / (60 * 4)))

        # those propertied depend on the task tree
        self._sc_path = []
        self._sc_priority = 0 if self._sl_priority is None else int(self._sl_priority)
        self._sc_start = None
        self._sc_due = None
        self._sc_next_sibling = None
        self._sc_prev_sibling = None

        """
        Dynamic properties
            - Depend on the current date
        """
        self._d_state = None


    @property
    def parent(self):
        return self._parent

    @property
    def indent(self):
        return self._sl_indent

    @property
    def is_leaf(self):
        return len(self._children) == 0

    @property
    def is_ready(self):
        return self._sc_type == self.TASK_TYPE_READY

    @property
    def is_done(self):
        return self._sc_type == self.TASK_TYPE_DONE

    @property
    def is_active(self):
        # the task can be executed (i.e. it's it's ready and it's leaf)
        # decide is the task is active
        return self.is_ready and self.is_leaf

    @property
    def is_root(self):
        return self._parent is None

    def __str__(self):
        return (
            "|".join([
                f"index: {self._index}",
                f"children_count: {len(self._children)}",
                f"d_state: {self._d_state}",
                f"f_line_num: {self._f_line_num}",
                f"f_subject: {self._f_subject}",
                f"sc_due: {self._sc_due}",
                f"sc_effort_days: {self._sc_effort_days}",
                f"sc_effort_minutes: {self._sc_effort_minutes}",
                f"sc_is_hard: {self._sc_is_hard}",
                f"sc_is_recurrent: {self._sc_is_recurrent}",
                f"sc_path: {self._sc_path}",
                f"sc_priority: {self._sc_priority}",
                f"sc_start: {self._sc_start}",
                f"sc_type: {self._sc_type}",
                f"sl_done: {self._sl_done}",
                f"sl_due_abs: {self._sl_due_abs}",
                f"sl_due_rel_unit: {self._sl_due_rel_unit}",
                f"sl_due_rel_value: {self._sl_due_rel_value}",
                f"sl_effort_unit: {self._sl_effort_unit}",
                f"sl_effort_value: {self._sl_effort_value}",
                f"sl_indent: {self._sl_indent}",
                f"sl_priority: {self._sl_priority}",
                f"sl_rec_interval: {self._sl_rec_interval}",
                f"sl_rec_period: {self._sl_rec_period}",
                f"sl_rec_type: {self._sl_rec_type}",
                f"sl_signal: {self._sl_signal}",
                f"sl_start: {self._sl_start}",
                f"sl_title: {self._sl_title}"
            ])
        )

    def add_child(self, other):
        # add the child to the list
        self._children.append(other)
        other._parent = self

        # add links between sibling children
        if len(self._children) > 1:
            self._children[-2]._sc_next_sibling = self._children[-1]
            self._children[-1]._sc_prev_sibling = self._children[-2]

    def raise_error(self, msg, error_cls=LogicError):
        raise error_cls(self._f_subject, self._f_line_num, msg)

    def _build(self, holidays, path=[], index="0"):
        """
        Rules enforced at individual task level:
            OK - A "recurrent" task must have a start date.
            OK - A task with a relative due date must have an explicit start date.
            - A start date must come before the end date.
            - A "hard" task requires an end date.
            - A "recurrent" task must not have an absolute end date.
            - The start date must come before the absolute end date.

        Rules enforced at parent / child level:
            OK - If "start date" of a task is not defined than it inherits from the parent.
            OK - A task must not explicitly start before it's parents.
            - A "recurrent" task cannot be the child of task with a due date.
            - A "recurrent" task cannot have children tasks.
            - A "parent" task needs to have at least one "active" child.
            - All task must end before their parents.
            - The "priority" of a task is the max between it's own priority and it's parents.
            - A "pending" tasks must be preceded by an "active" task
        """
        self._index = index

        if self.is_root:
            # this is the root of all tree
            self._sc_path = path
            self._sc_start = FIRST_START
            self._sc_due = LAST_DUE
            self._sc_priority = 0

        else:
            """
            Build the path
            """
            self._sc_path = path + [self._sl_title]

            """
            Compute priority
            """
            self._sc_priority = max(self._sc_priority, self._parent._sc_priority)

            """
            Compute start date
            """
            if self._sc_is_recurrent and (self._sl_start is None):
                self.raise_error("A recurrent task must have an explicit start date")

            if self._sl_start is None:
                # a taks without explicit start date inherits from its parents
                self._sc_start = self._parent._sc_start
            else:
                self._sc_start = get_date(self._sl_start)

            if self._sc_start < self._parent._sc_start:
                self.raise_error("Task can't start before their parents.")

            """
            Compute the due date
            """
            if (self._sl_due_abs is None) and (self._sl_due_rel_value is None):
                # a taks without explicit due date inherits from its parents
                self._sc_due = self._parent._sc_due

            elif self._sl_due_abs is not None:
                self._sc_due = get_date(self._sl_due_abs)

            else:
                if (self._sl_due_rel_value is not None) and (self._sl_start is None):
                    self.raise_error("A task with a relative due date must have an explicit start date")

                self._sc_due = get_date_relative(self._sc_start, int(self._sl_due_rel_value), self._sl_due_rel_unit, holidays)

            if self._sc_due > self._parent._sc_due:
                self.raise_error(f"A task can't be due ({self._sc_due}) after their parents due date ({self._parent._sc_due}).")

            elif self._sc_due < self._sc_start:
                self.raise_error(f"A task's due date ({self._sc_due}) can't come before start date ({self._sc_start}).")

            # if a due date is explicitly indicated an effort must be indicated
            if ((self._sl_due_abs is not None) or (self._sl_due_rel_value is not None)) and (self._sl_effort_value is None):
                self.raise_error(f"An effort must be specified every time a due date is specified.")

            # check due date for hard deadline tasks
            if self._sc_is_hard and (self._sl_due_abs is None) and (self._sl_due_rel_value is None):
                self.raise_error("Hard deadline tasks require an explicit due date.")

            # check active previous siblings for waiting tasks
            if (self._sc_type == self.TASK_TYPE_WAITING):

                if self._sc_is_recurrent:
                    self.raise_error("Recurrent tasks can't be pending other tasks.")

                if not self.is_leaf:
                    self.raise_error("Only leaf tasks can be pending other tasks.")

                if self._sc_prev_sibling._sc_is_recurrent:
                    self.raise_error("Tasks can't be pending recurrent tasks.")

                if self._sc_prev_sibling._sc_type != self.TASK_TYPE_READY:
                    self.raise_error("Waiting tasks needs must be pending a ready task.")

        # build recursively
        if self.is_leaf:
            if self._sl_effort_value == 0:
                self.raise_error("Tasks can't wait for recurrent tasks.")
            
            return self.is_ready

        else:
            has_ready_children = False

            for i, child in enumerate(self._children):
                has_ready_children = has_ready_children or child.is_ready

                child._build(holidays, self._sc_path, index + f".{i}")

            if (self.is_ready) and (not has_ready_children):
                if self.is_root:
                    self.raise_error("No tasks found.")
                else:
                    self.raise_error("No ready children found for ready parent.")

    def build(self, holidays):
        assert self.is_root, "`build` function can only be called by root"

        self._build(holidays)

        return self

    def _compute_state_today(self, today, holidays):
        MARGIN_DAYS = 3

        # add 3 slack days for hard due date tasks
        slack_margin = MARGIN_DAYS if self._sc_is_hard else 0
        effort_days = self._sc_effort_days

        date_limit_critical = add_business_days(self._sc_due, -(slack_margin + effort_days), holidays)
        date_limit_overdue  = add_business_days(self._sc_due, -slack_margin, holidays)

        if self._sc_type == self.TASK_TYPE_DONE:
            self._d_state = self.TASK_STATE_DONE

        elif (self._sc_type == self.TASK_TYPE_WAITING) or (self._sc_start > today):
            self._d_state = self.TASK_STATE_WAITING

        elif not self.is_leaf:
            self._d_state = self.TASK_STATE_NO_ACTION

        elif date_limit_overdue <= today:
            if self._sc_is_hard:
                self._d_state = self.TASK_STATE_NOW
            else:
                self._d_state = self.TASK_STATE_OVERDUE

        elif date_limit_critical <= today:
            self._d_state = self.TASK_STATE_CRITICAL

        else:
            self._d_state = self.TASK_STATE_ACTIVE

        for child in self._children:
            child._compute_state_today(today, holidays)

    def compute_state_today(self, today, holidays):
        assert self.is_root, "`compute_state_today` function can only be called by root"

        self._compute_state_today(today, holidays)

        return self

    def as_dict(self):
        return {
            'task':           self,
            'subject':        self._f_subject,
            'line_num':       self._f_line_num,
            'is_active':      self.is_active,
            'is_done':        self.is_done,
            'state':          self._d_state,
            'path':           self._sc_path,
            'indent':         self._sl_indent,
            'signal':         self._sl_signal,
            'title':          self._sl_title,
            'priority':       self._sc_priority,
            'start':          self._sc_start,
            'due':            self._sc_due,
            'effort_value':   self._sl_effort_value,
            'effort_unit':    self._sl_effort_unit,
            'effort_minutes': self._sc_effort_minutes,
            'effort_days':    self._sc_effort_days
        }


    def get_list(self):
        # do not include the root node in the list
        ret = [] if self.is_root else [self]

        for child in self._children:
            ret += child.get_list()

        return ret


