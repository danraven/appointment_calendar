import unittest
from uuid import UUID, uuid4
from datetime import datetime
from ..app.calendar import Calendar, Patient, SlotType

class CalendarLookupTestCase(unittest.TestCase):
    def setUp(self):
        self.calendar = Calendar(uuid4(), "Test Calendar")
        self.patients = [
            Patient(uuid4(), "Patient Foo"),
            Patient(uuid4(), "Patient Bar"),
            Patient(uuid4(), "Patient Baz")
        ]
        self.slot_types = [
            SlotType(uuid4(), "Free Consultation"),
            SlotType(uuid4(), "Videochat")
        ]

        slots = [
            (datetime(2020, 8, 17, 8, 30), datetime(2020, 8, 17, 10), self.slot_types[0]),
            (datetime(2020, 8, 17, 12, 30), datetime(2020, 8, 17, 16), self.slot_types[0]),
            (datetime(2020, 8, 17, 17), datetime(2020, 8, 17, 19), self.slot_types[1]),
            (datetime(2020, 8, 18, 8, 30), datetime(2020, 8, 18, 10, 30), self.slot_types[0])
        ]

        appointments = [
            (datetime(2020, 8, 17, 12, 30), datetime(2020, 8, 17, 13), self.patients[0]),
            (datetime(2020, 8, 17, 13, 30), datetime(2020, 8, 17, 14), self.patients[1])
        ]

        for time_start, time_end, slot_type in slots:
            self.calendar.allocate_time(time_start, time_end, slot_type)
        for time_start, time_end, patient in appointments:
            self.calendar.set_appointment(time_start, time_end, patient)

    def test_get_all(self):
        result = self.calendar.find_available_time()
        self.assertEqual(len(result), 5)

    def test_get_by_type(self):
        result = self.calendar.find_available_time(slot_type=self.slot_types[1])
        self.assertEqual(len(result), 1)

    def test_get_by_duration(self):
        result = self.calendar.find_available_time(duration=120)
        self.assertEqual(len(result), 3)

    def test_get_by_range(self):
        result = self.calendar.find_available_time(datetime(2020, 8, 17, 9), datetime(2020, 8, 17, 17, 30))
        self.assertEqual(len(result), 4)

    def test_get_empty(self):
        result = self.calendar.find_available_time(datetime(2020, 8, 20, 10), datetime(2020, 8, 20, 15))
        self.assertEqual(len(result), 0)

    def test_get_by_multiple_filters(self):
        result = self.calendar.find_available_time(datetime(2020, 8, 17, 9, 30), datetime(2020, 8, 17, 19), duration=60, slot_type=self.slot_types[0])
        self.assertEqual(len(result), 1)

if __name__ == "__main__":
    unittest.main()