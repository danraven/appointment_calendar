import unittest
from uuid import UUID, uuid4
from datetime import datetime
from ..app.calendar import Calendar, Patient, SlotType

class CalendarTestCase(unittest.TestCase):
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

    def test_allocate_time(self):
        time_from = datetime(2020, 8, 17, 8, 30)
        time_to = datetime(2020, 8, 17, 10)
        self.calendar.allocate_time(time_from, time_to, self.slot_types[0])
        self.assertEqual(len(self.calendar.timeslots), 1)
        slot = self.calendar.timeslots[0]
        self.assertEqual(slot.time_from, time_from)
        self.assertEqual(slot.time_to, time_to)
        self.assertTrue(slot.is_type(self.slot_types[0]))
        self.assertTrue(slot.is_available())
        self.assertEqual(slot.get_duration(), 90)

    def test_allocate_multiple_time(self):
        time_first_from = datetime(2020, 8, 17, 8, 30)
        time_first_to = datetime(2020, 8, 17, 10)
        time_second_from = datetime(2020, 8, 17, 13)
        time_second_to = datetime(2020, 8, 17, 15, 30)

        self.calendar.allocate_time(time_second_from, time_second_to, self.slot_types[0])
        self.calendar.allocate_time(time_first_from, time_first_to, self.slot_types[0])
        self.assertEqual(len(self.calendar.timeslots), 2)

        first_slot = self.calendar.timeslots[0]
        second_slot = self.calendar.timeslots[1]
        self.assertEqual(first_slot.time_from, time_first_from)
        self.assertEqual(second_slot.time_from, time_second_from)

    def test_allocate_overlap(self):
        self.calendar.allocate_time(datetime(2020, 8, 17, 8, 30), datetime(2020, 8, 17, 10), self.slot_types[0])
        with self.assertRaisesRegex(ValueError, "There is already"):
            self.calendar.allocate_time(datetime(2020, 8, 17, 9, 45), datetime(2020, 8, 17, 11), self.slot_types[0])

    def test_allocate_merge_behind(self):
        time_from = datetime(2020, 8, 17, 8, 30)
        time_split = datetime(2020, 8, 17, 10)
        time_to = datetime(2020, 8, 17, 11, 30)

        self.calendar.allocate_time(time_from, time_split, self.slot_types[0])
        self.calendar.allocate_time(time_split, time_to, self.slot_types[0])

        self.assertEqual(len(self.calendar.timeslots), 1)
        slot = self.calendar.timeslots[0]
        self.assertEqual(slot.time_from, time_from)
        self.assertEqual(slot.time_to, time_to)

    def test_allocate_merge_forward(self):
        time_from = datetime(2020, 8, 17, 8, 30)
        time_split = datetime(2020, 8, 17, 10)
        time_to = datetime(2020, 8, 17, 11, 30)

        self.calendar.allocate_time(time_split, time_to, self.slot_types[0])
        self.calendar.allocate_time(time_from, time_split, self.slot_types[0])

        self.assertEqual(len(self.calendar.timeslots), 1)
        slot = self.calendar.timeslots[0]
        self.assertEqual(slot.time_from, time_from)
        self.assertEqual(slot.time_to, time_to)

    def test_allocate_no_merge(self):
        time_from = datetime(2020, 8, 17, 8, 30)
        time_split = datetime(2020, 8, 17, 10)
        time_to = datetime(2020, 8, 17, 11, 30)

        self.calendar.allocate_time(time_from, time_split, self.slot_types[0])
        self.calendar.allocate_time(time_split, time_to, self.slot_types[1])

        self.assertEqual(len(self.calendar.timeslots), 2)

    def test_schedule_appointment(self):
        free_from = datetime(2020, 8, 17, 8, 30)
        free_to = datetime(2020, 8, 17, 10)
        appointment_from = datetime(2020, 8, 17, 9)
        appointment_to = datetime(2020, 8, 17, 9, 30)
        self.calendar.allocate_time(free_from, free_to, self.slot_types[0])
        self.calendar.set_appointment(appointment_from, appointment_to, self.patients[0])

        self.assertEqual(len(self.calendar.timeslots), 3)
        split_before = self.calendar.timeslots[0]
        split_appointment = self.calendar.timeslots[1]
        split_after = self.calendar.timeslots[2]
        self.assertEqual(split_before.time_from, free_from)
        self.assertEqual(split_before.time_to, appointment_from)
        self.assertEqual(split_appointment.time_from, appointment_from)
        self.assertEqual(split_appointment.time_to, appointment_to)
        self.assertEqual(split_after.time_from, appointment_to)
        self.assertEqual(split_after.time_to, free_to)
        self.assertFalse(split_appointment.is_available())
        self.assertTrue(split_before.is_available())
        self.assertTrue(split_after.is_available())

    def test_schedule_overlap(self):
        self.calendar.allocate_time(datetime(2020, 8, 17, 8, 30), datetime(2020, 8, 17, 10), self.slot_types[0])
        self.calendar.set_appointment(datetime(2020, 8, 17, 8, 30), datetime(2020, 8, 17, 9, 30), self.patients[0])
        self.assertEqual(len(self.calendar.timeslots), 2)
        with self.assertRaisesRegex(ValueError, "outside of the time slot"):
            self.calendar.set_appointment(datetime(2020, 8, 17, 9, 15), datetime(2020, 8, 17, 9, 45), self.patients[1])

    def test_schedule_too_long(self):
        self.calendar.allocate_time(datetime(2020, 8, 17, 8, 30), datetime(2020, 8, 17, 10), self.slot_types[0])
        with self.assertRaisesRegex(ValueError, "interval outside"):
            self.calendar.set_appointment(datetime(2020, 8, 17, 9, 15), datetime(2020, 8, 17, 10, 30), self.patients[1])

    def test_schedule_whole_block(self):
        time_from = datetime(2020, 8, 17, 8, 30)
        time_to = datetime(2020, 8, 17, 10)
        self.calendar.allocate_time(time_from, time_to, self.slot_types[0])
        self.calendar.set_appointment(time_from, time_to, self.patients[0])
        self.assertEqual(len(self.calendar.timeslots), 1)

if __name__ == "__main__":
    unittest.main()