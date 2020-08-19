import argparse
import json
from datetime import datetime
from os import path
from uuid import UUID
from typing import Iterable
from pathlib import Path
from .app.calendar import Calendar, Patient, SlotType

BASE_PATH = path.dirname(__file__)

class CalendarSearch:
    def __init__(self):
        self.patients = {}
        self.slot_types = {}
        self.calendars = {}

    def load_slot_types(self):
        for row in json.loads(Path(path.join(BASE_PATH, "data/slottypes.json")).read_text()):
            if row['id'] in self.slot_types.keys():
                continue
            self.slot_types[row['id']] = SlotType(UUID(row['id']), "%s (%s)" % (row['name'], row['slot_size']))

    def load_calendar(self, json_name: str, id: UUID, name: str):
        data = json.loads(Path(path.join(BASE_PATH, "data/%s.json" % json_name)).read_text())
        calendar = Calendar(id, name)
        for patient_id, patient_row in data['patient_meta'].items():
            if patient_id in self.patients.keys():
                continue
            self.patients[patient_id] = Patient(UUID(patient_id), "%s %s" % (patient_row['firstname'], patient_row['lastname']))
        for slot_row in data['timeslots']:
            calendar.allocate_time(datetime.fromisoformat(slot_row['start']), datetime.fromisoformat(slot_row['end']), self.slot_types[slot_row['type_id']])
        for a_row in data['appointments']:
            calendar.set_appointment(datetime.fromisoformat(a_row['start']), datetime.fromisoformat(a_row['end']), self.patients[a_row['patient_id']])
        self.calendars[str(id)] = calendar

    def find_available_time(self, calendars: Iterable[UUID], duration: int=0, time_from: datetime=None, time_to: datetime=None, slot_type_id: UUID=None):
        results = {}
        for entry in calendars:
            id_str = str(entry)
            slot_type = self.slot_types[str(slot_type_id)]
            if id_str not in self.calendars.keys():
                raise ValueError("Calendar ID not found")
            results[id_str] = self.calendars[id_str].find_available_time(time_from, time_to, duration=duration, slot_type=slot_type)
        return results

def str_to_datetime(val):
    if not val:
        return None
    return datetime.strptime(val, "%Y-%m-%d %H:%M")

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calendar", help="ID of a calendar to search in", type=UUID, action="append")
    parser.add_argument("-f", "--time_from", help="Start of timeframe", type=str_to_datetime)
    parser.add_argument("-t", "--time_to", help="End of timeframe", type=str_to_datetime)
    parser.add_argument("-d", "--duration", help="Minimum duration of time slots", type=int, default=0)
    parser.add_argument("-s", "--slottype", help="Time slot type", type=UUID)

    search = CalendarSearch()
    search.load_slot_types()
    search.load_calendar("joanna_hef", UUID("48644c7a-975e-11e5-a090-c8e0eb18c1e9"), "Joanna Hef")
    search.load_calendar("danny_boy", UUID("48cadf26-975e-11e5-b9c2-c8e0eb18c1e9"), "Danny Boy")
    search.load_calendar("emma_win", UUID("452dccfc-975e-11e5-bfa5-c8e0eb18c1e9"), "Emma Win")

    args = parser.parse_args()
    if not args.calendar:
        raise ValueError("Must provide at least one calendar")
    results = search.find_available_time(args.calendar, args.duration, args.time_from, args.time_to, args.slottype)
    for cid, result in results.items():
        calendar = search.calendars[cid]
        if not len(result):
            print("No available slots for %s\n" % calendar.name)
            continue
        print("Available slots for %s (%d):\n" % (calendar.name, len(result)))
        for slot in result:
            print("%s - %s (%s)" % (slot.time_from.strftime("%Y-%m-%d %H:%M"), slot.time_to.strftime("%H:%M"), slot.type.name))
        print("\n")

if __name__ == "__main__":
    run()