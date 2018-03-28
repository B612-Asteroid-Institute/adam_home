"""
    timer.py
"""

import datetime


class Timer:
    def __init__(self):
        self.stack = []

    def start(self, description):
        self.stack.append([description, datetime.datetime.now()])

    def stop(self):
        latest = self.stack.pop()
        time_diff = (datetime.datetime.now() - latest[1]).total_seconds()
        print("[" + str(time_diff) + "] " + latest[0])
