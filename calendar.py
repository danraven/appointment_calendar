from datetime import datetime
from copy import copy

class Patient:
    def __init__(self, id: str, name: str):
        self._id = id
        self.name = name

class SlotType:
    def __init__(self, id: str, name: str):
        self._id = id
        self.name = name

class Appointment:
    def __init__(self, patient: Patient):
        self.patient = patient
    
class TimeSlot:
    def __init__(self, time_from: datetime, time_to: datetime, slot_type: SlotType):
        if time_to <= time_from:
            raise ValueError("Start time must be before end time")
        self.time_from = time_from
        self.time_to = time_to
        self.type = slot_type
        self.appointment = None
        self.calendar = None
    
    def get_duration(self):
        delta = self.time_to - self.time_from
        return delta.total_seconds() / 60

    def split_by_interval(self, time_from: datetime, time_to: datetime):
        if time_to <= time_from:
            raise ValueError("Start time must be before end time")
        if time_from < self.time_from or time_to > self.time_to:
            raise ValueError("Cannot split by an interval outside of the time slot")
        if not self.is_available():
            raise Exception("Cannot split a time slot that already has an appointment assigned to")
        cut_part = copy(self)
        cut_part.time_from = time_from
        cut_part.time_to = time_to
        parts = [cut_part]
        if time_from > self.time_from:
            before_part = copy(self)
            before_part.time_to = time_from
            parts.append(before_part)
        if time_to < self.time_to:
            after_part = copy(self)
            after_part.time_from = time_to
            parts.append(after_part)
        return tuple(parts)

    def is_available(self):
        return not self.appointment

class Calendar:
    def __init__(self, id: str, name: str):
        self._id = id
        self.name = name
        self.timeslots = {}
