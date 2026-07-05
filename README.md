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

## ✨ Features

What the finished app actually implements (algorithms detailed in
[Smarter Scheduling](#-smarter-scheduling)):

**Scheduling algorithms**

- **Sorting by time** — orders a day's tasks morning → night using the `TimeOfDay` `IntEnum` (`CarePlanner.sort_by_time`).
- **Conflict warnings** — flags any tasks sharing the same time slot (across one or many pets) as human-readable warnings; never raises (`CarePlanner.detect_conflicts`).
- **Daily / weekly recurrence** — completing a recurring task auto-schedules its next occurrence, advancing the due date by +1 day (daily) or +7 days (weekly); one-off tasks don't recur (`CarePlanner.mark_task_complete` + `CareItem.recurrence`).
- **Occurrence rules** — each care item decides if it's due on a date: meals/walks on chosen weekdays (or every day), medications across an inclusive start–end range, grooming on a single calendar day (`CareItem.occurs_on`).
- **Filtering** — narrow a plan by pet name (case-insensitive) or by completion status (`CarePlanner.filter_by_pet`, `filter_by_status`).
- **Explainable plans** — every plan carries a generated reasoning string summarizing task counts by kind (`CarePlanner._explain_reasoning`).

**Domain & app**

- **Owner accounts** — sign up / sign in with salted PBKDF2-HMAC-SHA256 password hashing.
- **Pet management** — add/remove pets, each holding its own meals, medications, walks, and grooming appointments.
- **Polymorphic care items** — `Meal`, `Medication`, `Walk`, and `GroomingAppointment` share one `CareItem` interface (`describe`, `occurs_on`, `recurrence`), so the planner treats them uniformly and new kinds slot in without changing it.
- **Owner-wide planning** — builds one `DailyPlan` per pet for a given day across all of an owner's pets (`CarePlanner.generate_daily_plans_for_owner`).
- **Weekly shopping cart** — derived automatically from recurring care items, with quantities inferred from how often each item recurs (`Pet.build_shopping_cart`).
- **Streamlit UI** — add pets and tasks, generate today's plan, and view a sorted, filterable table with conflict warnings surfaced up top.

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
python -m pytest

```
system reliability: 4.5 stars 
These 10 tests cover PawPal+'s core care-planning logic: marking tasks complete, adding care items to a pet, and sorting a day's tasks into chronological order (morning → night). They verify recurrence — a completed daily task spawns the next day's occurrence, including across a year boundary, while one-off tasks don't recur. They also check conflict detection (two tasks in the same time slot raise a warning, distinct slots stay silent) plus edge cases: a pet with no tasks yields an empty plan, and medication courses fall due on their inclusive start/end dates.
======== test session starts =========================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\pakoj41074\Desktop\ai engineering\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 10 items                                                    

test_pawpal.py ..........                                       [100%]

========================= 10 passed in 0.43s =========================
```

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

PawPal+ has two front doors: an interactive **Streamlit app** (`app.py`) for the
pet owner, and a scripted **CLI demo** (`main.py`) that exercises every scheduling
algorithm end to end.

### The Streamlit UI

Launch it with `streamlit run app.py`. The page is organized top-to-bottom into
the actions an owner takes:

- **Add a Pet** — enter name, species, breed, and age; submitting adds the pet
  and it appears in a "Your pets" table (with a per-pet count of care items).
- **Schedule a Task** — pick one of your pets, give the task a title, duration,
  and priority. Priority maps onto a time of day (high → morning, medium →
  midday, low → evening) so higher-priority tasks land earlier in the day.
- **Today's Schedule** — click **Generate schedule** to build the plan across all
  your pets for today. The result is one unified, professional table you can
  **filter** by pet or by status (all / to-do / completed).

### Example workflow

1. **Add a pet** — e.g. "Mochi", a 2-year-old cat. It shows up in the pets table.
2. **Add a second pet** — e.g. "Rex", a dog, so the schedule spans multiple pets.
3. **Schedule tasks** — give Rex a high-priority "Morning walk" and a high-priority
   "Morning meds" (both map to the morning slot), plus an evening task for Mochi.
4. **Generate the schedule** — the plan builds instantly for the current day.
5. **Read the results** — tasks are listed morning → night, and you can filter the
   table down to just Rex or just the tasks still to do.

### Key Scheduler behaviors you'll see

- **Sorting by time** — the table is always ordered morning → night, regardless of
  the order tasks were added, because entries sort on the `TimeOfDay` `IntEnum`.
- **Conflict warnings** — because both of Rex's morning tasks share the morning
  slot, the app surfaces a ⚠️ warning **above** the table naming the pet, the two
  tasks, and the slot — so the clash is impossible to miss before you read the plan.
  With no clashes, a green ✅ "no conflicts" message confirms the day is clear.
- **Filtering** — the pet and status dropdowns narrow the same plan without
  rebuilding it, and conflicts are still checked against the *full* day (hiding a
  pet never hides a real-world overlap).
- **Recurrence & explainability** are visible in the CLI demo below: completing a
  daily task auto-schedules tomorrow's occurrence, and every plan reports the
  reasoning behind it.

### Sample CLI output (`python main.py`)

The demo signs up an owner, registers two pets (Rex and Mochi), schedules tasks
at different times — including two in Rex's morning slot to trigger a conflict —
then prints the plan and runs every algorithm over it:

```text
============================================
Today's Schedule — Sunday, July 05, 2026
Owner: Jayden
============================================

Rex (Dog)
  [MORNING  ] Meal: 150g of Kibble (Morning) — one scoop
  [MORNING  ] Medication: Heartgard 1 chew, 1x/day — give with breakfast
  [MIDDAY   ] Grooming: Bath & brush with Happy Paws at 2026-07-05 12:30 (confirmed) — nail trim too
  [AFTERNOON] Walk: 30 min via Riverside loop (Afternoon) — keep it on-leash

Mochi (Cat)
  [EVENING  ] Meal: 85g of Wet food (Evening)
  [NIGHT    ] Medication: Amitriptyline 5mg, 1x/day — with food

============================================
All tasks sorted by time of day
============================================
  [MORNING  ] Rex: Meal: 150g of Kibble (Morning) — one scoop
  [MORNING  ] Rex: Medication: Heartgard 1 chew, 1x/day — give with breakfast
  [MIDDAY   ] Rex: Grooming: Bath & brush with Happy Paws at 2026-07-05 12:30 (confirmed) — nail trim too
  [AFTERNOON] Rex: Walk: 30 min via Riverside loop (Afternoon) — keep it on-leash
  [EVENING  ] Mochi: Meal: 85g of Wet food (Evening)
  [NIGHT    ] Mochi: Medication: Amitriptyline 5mg, 1x/day — with food

Filter by pet — Rex has 4 task(s) today.

Completed 'Meal: 150g of Kibble (Morning) — one scoop' (frequency: DAILY).
  -> auto-scheduled next occurrence for Monday, Jul 06.

Filter by status — 1 done, 5 pending.

============================================
Conflict check
============================================
  WARNING: Conflict at Morning: 2 tasks overlap (Rex — Meal: 150g of Kibble (Morning) — one scoop; Rex — Medication: Heartgard 1 chew, 1x/day — give with breakfast).
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

