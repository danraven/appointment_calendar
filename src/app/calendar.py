from datetime import datetime, timedelta
from bisect import bisect_left, bisect_right
from uuid import UUID
from copy import copy

class Patient:
    def __init__(self, id: UUID, name: str):
        self._id = id
        self.name = name

class SlotType:
    def __init__(self, id: UUID, name: str):
        self._id = id
        self.name = name

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
            raise ValueError("Cannot split a time slot that already has an appointment assigned to")
        cut_part = copy(self)
        cut_part.time_from = time_from
        cut_part.time_to = time_to
        parts = []
        if time_from > self.time_from:
            before_part = copy(self)
            before_part.time_to = time_from
            parts.append(before_part)
        parts.append(cut_part)
        if time_to < self.time_to:
            after_part = copy(self)
            after_part.time_from = time_to
            parts.append(after_part)
        return tuple(parts)

    def is_available(self):
        return not self.appointment

    def is_type(self, slot_type: SlotType=None):
        if not slot_type:
            return True
        return slot_type._id == self.type._id

class Appointment:
    def __init__(self, patient: Patient, slot: TimeSlot):
        self.patient = patient
        self.slot = slot
        self.slot.appointment = self

class Calendar:
    def __init__(self, id: UUID, name: str):
        self._id = id
        self.name = name
        self.timeslots = []
        self._start_indices = []
        self._end_indices = []

    def allocate_time(self, time_from: datetime, time_to: datetime, slot_type: SlotType):
        if time_to <= time_from:
            raise ValueError("Start time must be before end time")
        after_index = bisect_right(self._end_indices, time_from.timestamp())
        before_index = bisect_left(self._start_indices, time_to.timestamp(), after_index)
        if before_index != after_index:
            raise ValueError("There is already time allocated to this interval")
        if after_index > 0 and self._end_indices[after_index - 1] == time_from.timestamp():
            prev_slot = self.timeslots[after_index - 1]
            if prev_slot.is_available() and prev_slot.is_type(slot_type):
                prev_slot.time_to = time_to
                self._end_indices[after_index - 1] = time_to.timestamp()
                return prev_slot
        if after_index < len(self.timeslots) and self._start_indices[after_index] == time_to.timestamp():
            next_slot = self.timeslots[after_index]
            if next_slot.is_available() and next_slot.is_type(slot_type):
                next_slot.time_from = time_from
                self._start_indices[after_index] = time_from.timestamp()
                return next_slot
        slot = TimeSlot(time_from, time_to, slot_type)
        slot.calendar = self
        self.timeslots.insert(after_index, slot)
        self._start_indices.insert(after_index, time_from.timestamp())
        self._end_indices.insert(after_index, time_to.timestamp())
        return slot

    def set_appointment(self, time_from: datetime, time_to: datetime, patient: Patient):
        duration = (time_to - time_from).total_seconds() / 60
        idx = bisect_right(self._start_indices, time_from.timestamp())
        if not idx:
            raise ValueError("There is no allocated time for this appointment")
        idx = idx - 1
        if self.timeslots[idx].get_duration() < duration:
            raise ValueError("There is not enough time allocated for this appointment")

        slot = self.timeslots[idx]
        if not slot.is_available():
            raise ValueError("There is already an appointment in this interval")
        parts = slot.split_by_interval(time_from, time_to)
        appointment = None
        del self._start_indices[idx]
        del self._end_indices[idx]
        del self.timeslots[idx]

        for i, slot_part in enumerate(parts):
            if slot_part.time_from == time_from:
                appointment = Appointment(patient, slot_part)
            self.timeslots.insert(idx + i, slot_part)
            self._start_indices.insert(idx + i, slot_part.time_from.timestamp())
            self._end_indices.insert(idx + i, slot_part.time_to.timestamp())

        return appointment

    def find_available_time(self, time_from: datetime=None, time_to: datetime=None, slot_type: SlotType=None, duration: int=0):
        time_from = datetime.now() - timedelta(days=365) if not time_from else time_from
        time_to = datetime.now() + timedelta(days=365) if not time_to else time_to

        start_index = bisect_left(self._start_indices, time_from.timestamp())
        end_index = bisect_left(self._end_indices, time_to.timestamp())
        if start_index > 0 and self.timeslots[start_index - 1].time_to > time_from:
            start_index = start_index - 1
        if end_index < len(self.timeslots) - 1 and self.timeslots[end_index + 1].time_from < time_to:
            end_index = end_index + 1

        if start_index > end_index or start_index == len(self.timeslots):
            return []

        return list(filter(lambda slot: slot.is_available() and slot.get_duration() >= duration and slot.is_type(slot_type), self.timeslots[start_index:end_index]))