# Calendar time allocator and appointment setter

## Description

A small tool that allows patients to view available time frames to schedule appointments with doctors.

## Requirements

* Python 3.8^

## Usage

Run from the command line as a module with `python -m timeallocator`.
The following options can/must be provided:

* `-c --calendar <UUID>`: **Required**. The ID of the calendar to search in. Can be defined multiple times.
* `-f --time_from "%Y-%m-%d %H:%M"`: Start of the search time frame. Defaults to `<now> - 365 days`.
* `-t --time_to "%Y-%m-%d %H:%M"`: End of the search time frame. Defaults to `<now> + 365 days`.
* `-d --duration <int>`: Minimum duration of the available time slots (in minutes). Defaults to 0.
* `-s --slottype <UUID>`: The type of time slot to look for. By default any type is returned.

## Test

Tests can be run with `python -m unittest`.