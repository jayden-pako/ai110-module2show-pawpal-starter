# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output
```
============================================
Today's Schedule — Sunday, July 05, 2026
Owner: Jayden
============================================

Rex (Dog)
  [MORNING  ] Meal: 150g of Kibble (Morning) — one scoop
  [MIDDAY   ] Grooming: Bath & brush with Happy Paws at 2026-07-05 12:30 (confirmed) — nail trim too
  [AFTERNOON] Walk: 30 min via Riverside loop (Afternoon) — keep it on-leash

Mochi (Cat)
  [EVENING  ] Meal: 85g of Wet food (Evening)
  [NIGHT    ] Medication: Amitriptyline 5mg, 1x/day — with food

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
======================== test session starts =========================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\pakoj41074\Desktop\ai engineering\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 2 items                                                     

test_pawpal.py ..                                               [100%]

========================= 2 passed in 0.47s ==========================
```

## 📐 Smarter Scheduling

The scheduling algorithms live on `CarePlanner` in [`pawpal_system.py`](pawpal_system.py)
and operate on `PlanEntry` objects (one time-slotted task within a day's plan).
The demo in [`main.py`](main.py) exercises all four features end to end.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `CarePlanner.sort_by_time()` | Orders tasks morning → night by their `TimeOfDay` |
| Filtering | `CarePlanner.filter_by_pet()`, `CarePlanner.filter_by_status()` | By pet name (case-insensitive) or completion status |
| Conflict handling | `CarePlanner.detect_conflicts()` | Warns on tasks sharing the same time slot; never raises |
| Recurring tasks | `CarePlanner.mark_task_complete()` + `CareItem.recurrence()` | Completing a daily/weekly task auto-schedules the next |

### Sorting behavior — `CarePlanner.sort_by_time()`

Returns a list of `PlanEntry` ordered chronologically from morning to night.
Because `TimeOfDay` is an `IntEnum`, a single `sorted(entries, key=lambda e: e.time_of_day)`
does the work. (The same lambda-key pattern would sort zero-padded `"HH:MM"`
strings correctly too, since they compare lexicographically.)

### Filtering behavior — `filter_by_pet()` / `filter_by_status()`

- `filter_by_pet(entries, pet_name)` — returns only the entries belonging to the
  named pet, matched case-insensitively.
- `filter_by_status(entries, completed)` — returns only the entries whose
  completion state matches the `completed` flag (e.g. all pending, or all done).

Each entry carries a denormalized `pet_name` and `completed` flag so these
filters run over one flat list of tasks across every pet.

### Conflict detection — `CarePlanner.detect_conflicts()`

A lightweight check that groups all entries by their `TimeOfDay` slot and returns
a human-readable **warning string** for every slot holding more than one task
(across the same or different pets). It returns warnings rather than raising, so
the caller can print them and keep running. It flags exact same-slot collisions
only — see the tradeoff note in [`reflection.md`](reflection.md) (§2b).

### Recurring task logic — `mark_task_complete()` + `CareItem.recurrence()`

Each care item answers `recurrence()` polymorphically (`DAILY`, `WEEKLY`, or
`NONE`): meals/walks are daily unless bound to specific weekdays, medications are
daily, and one-off grooming appointments don't recur. When
`CarePlanner.mark_task_complete(entry)` marks a recurring task done, it returns a
fresh `PlanEntry` for the next occurrence, advancing the due date with
`timedelta` (+1 day for daily, +7 for weekly). One-off tasks return `None`.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
