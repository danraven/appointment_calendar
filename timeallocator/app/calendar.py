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
        # Do some sanity checks
        if time_to <= time_from:
            raise ValueError("Start time must be before end time")
        if time_from < self.time_from or time_to > self.time_to:
            raise ValueError("Cannot split by an interval outside of the time slot")
        if not self.is_available():
            raise ValueError("Cannot split a time slot that already has an appointment assigned to")

        # Clone the time slot into 1-3 chunks and return it in a chronological order:
        # Free time slot before the appointment (if any is left)
        # The time slot with the appointment (always present)
        # Free time slot after the appointment (if any is left)
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
        # For the sake of querying, if no SlotType is passed this returns as a match, though it can be argued that it makes little sense
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
        # Time slots should be ordered by start/end date (and they cannot overlap)
        # Two helper lists are created in tandem that hold the start and end dates as timestamps for easier search.
        # They should be mutated along with the slots.
        self.timeslots = []
        self._start_indices = []
        self._end_indices = []

    def allocate_time(self, time_from: datetime, time_to: datetime, slot_type: SlotType):
        # Basic sanity check
        if time_to <= time_from:
            raise ValueError("Start time must be before end time")
        # Get the index that's:
        # 1. after the slot that ends before our start time
        # 2. before our end time
        after_index = bisect_right(self._end_indices, time_from.timestamp())
        before_index = bisect_left(self._start_indices, time_to.timestamp(), after_index)
        # If all's correct it both should point to the same spot, otherwise there's an overlap
        if before_index != after_index:
            raise ValueError("There is already time allocated to this interval")
        # Lookbehind: if there is a slot before that ends exactly as ours begin, is available and is of the same type, we just extend and return that
        if after_index > 0 and self._end_indices[after_index - 1] == time_from.timestamp():
            prev_slot = self.timeslots[after_index - 1]
            if prev_slot.is_available() and prev_slot.is_type(slot_type):
                prev_slot.time_to = time_to
                self._end_indices[after_index - 1] = time_to.timestamp()
                return prev_slot
        # Lookahead: same with the slot after
        # TODO: Implement merging; two slots with a hole between them should be merged into one if time is allocated there
        if after_index < len(self.timeslots) and self._start_indices[after_index] == time_to.timestamp():
            next_slot = self.timeslots[after_index]
            if next_slot.is_available() and next_slot.is_type(slot_type):
                next_slot.time_from = time_from
                self._start_indices[after_index] = time_from.timestamp()
                return next_slot
        # Otherwise just create the new time slot and insert it into its place
        slot = TimeSlot(time_from, time_to, slot_type)
        slot.calendar = self
        self.timeslots.insert(after_index, slot)
        self._start_indices.insert(after_index, time_from.timestamp())
        self._end_indices.insert(after_index, time_to.timestamp())
        return slot

    def set_appointment(self, time_from: datetime, time_to: datetime, patient: Patient):
        # Get the index right after the slot with an equal or earlier start date
        idx = bisect_right(self._start_indices, time_from.timestamp())
        if not idx:
            raise ValueError("There is no allocated time for this appointment")

        # Step back by one index to get the time frame the appointment might fit in
        idx = idx - 1
        slot = self.timeslots[idx]
        # The split function takes care of sanity checks, like whether there's already an appointment in this slot or if it's not long enough
        parts = slot.split_by_interval(time_from, time_to)
        appointment = None
        # Remove the old time slot and replace it with the splits
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
        # Go back/forward a year if no time range is set
        time_from = datetime.now() - timedelta(days=365) if not time_from else time_from
        time_to = datetime.now() + timedelta(days=365) if not time_to else time_to
        timestamp_from = time_from.timestamp()
        timestamp_to = time_to.timestamp()

        # Get an index range of timeslots to consider
        start_index = bisect_left(self._start_indices, timestamp_from)
        end_index = bisect_right(self._end_indices, timestamp_to, start_index)
        # If either index is out of bounds there are definitely no matches
        if start_index == len(self.timeslots) or not end_index:
            return []

        # If there's a time slot before that starts before but ends after the start time (with sufficient duration), include that to the list
        if start_index > 0 and (self._end_indices[start_index - 1] - timestamp_from) / 60 >= duration:
            start_index = start_index - 1
        # Similarly if there's a time slot after that starts before the end time, include that as well
        if end_index <= len(self.timeslots) - 1 and (timestamp_to - self._start_indices[end_index]) / 60 >= duration:
            end_index = end_index + 1

        # Filter down the matched candidates by availability, duration and slot type
        return list(filter(lambda slot: slot.is_available() and slot.get_duration() >= duration and slot.is_type(slot_type), self.timeslots[start_index:end_index]))