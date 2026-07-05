"""Tests for the PawPal care-planning algorithm.

Run with pytest:      pytest test_pawpal.py
Or standalone:        python test_pawpal.py
"""

from datetime import date

from pawpal_system import (
    CarePlanner,
    DayOfWeek,
    Frequency,
    Medication,
    Owner,
    Pet,
    PlanEntry,
    TimeOfDay,
    Walk,
)


def _walk(time_of_day, notes="", days=None):
    """Build a Walk that recurs on the given days (empty => every day)."""
    return Walk(
        item_id=0,
        time_of_day=time_of_day,
        notes=notes,
        duration_minutes=20,
        route="Block loop",
        days=list(days) if days else [],
    )


def test_mark_complete_changes_task_status():
    """Task Completion: mark_complete() flips a task's status to done."""
    # Build a pet with a single walk that occurs every day, then plan a day.
    pet = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)
    pet.schedule_walk(
        Walk(
            item_id=0,
            time_of_day=TimeOfDay.MORNING,
            notes="",
            duration_minutes=20,
            route="Block loop",
            days=[],  # empty => every day, so it lands on any date
        )
    )

    plan = CarePlanner().generate_daily_plan(pet, date(2026, 7, 6))
    task = plan.entries[0]

    # Precondition: a freshly planned task starts incomplete.
    assert task.completed is False

    task.mark_complete()

    # The status actually changed.
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet grows that pet's task count."""
    pet = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)

    # list_care_items() is the pet's full task list; start from its size.
    count_before = len(pet.list_care_items())

    pet.create_meal("Kibble", [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY])

    count_after = len(pet.list_care_items())

    assert count_after == count_before + 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------
def test_schedule_returns_tasks_in_chronological_order():
    """Sorting Correctness: a plan's tasks come out morning -> night.

    Attach walks OUT of chronological order (night, then morning, then midday)
    so a passing test proves the planner sorts rather than echoing insertion
    order.
    """
    pet = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)
    pet.schedule_walk(_walk(TimeOfDay.NIGHT, notes="late loop"))
    pet.schedule_walk(_walk(TimeOfDay.MORNING, notes="early loop"))
    pet.schedule_walk(_walk(TimeOfDay.MIDDAY, notes="noon loop"))

    plan = CarePlanner().generate_daily_plan(pet, date(2026, 7, 6))
    times = [entry.time_of_day for entry in plan.to_schedule()]

    assert times == [TimeOfDay.MORNING, TimeOfDay.MIDDAY, TimeOfDay.NIGHT]
    # And they are genuinely non-decreasing (works for any number of slots).
    assert times == sorted(times)


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------
def test_completing_daily_task_creates_task_for_next_day():
    """Recurrence Logic: completing a DAILY task yields the next day's task."""
    pet = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)
    pet.schedule_walk(_walk(TimeOfDay.MORNING, days=[]))  # empty => daily

    planner = CarePlanner()
    plan = planner.generate_daily_plan(pet, date(2026, 7, 6))
    task = plan.entries[0]
    assert task.frequency is Frequency.DAILY  # precondition

    next_task = planner.mark_task_complete(task)

    # The original is now done, and a fresh occurrence exists for the NEXT day.
    assert task.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date(2026, 7, 7)
    # The recurring identity carries over to the new occurrence.
    assert next_task.time_of_day == task.time_of_day
    assert next_task.frequency is Frequency.DAILY
    assert next_task.action == task.action


def test_completing_one_off_task_does_not_recur():
    """Recurrence Logic (edge): a one-off task has no next occurrence."""
    entry = PlanEntry(
        time_of_day=TimeOfDay.MORNING,
        action="One-time grooming",
        frequency=Frequency.NONE,
        due_date=date(2026, 7, 6),
    )

    next_task = CarePlanner().mark_task_complete(entry)

    assert entry.completed is True
    assert next_task is None  # nothing to reschedule


def test_completing_daily_task_rolls_over_year_boundary():
    """Recurrence Logic (edge): +1 day crosses the year boundary correctly."""
    entry = PlanEntry(
        time_of_day=TimeOfDay.MORNING,
        action="Evening meds",
        frequency=Frequency.DAILY,
        due_date=date(2026, 12, 31),
    )

    next_task = CarePlanner().mark_task_complete(entry)

    assert next_task is not None
    assert next_task.due_date == date(2027, 1, 1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------
def test_detect_conflicts_flags_duplicate_time_slot():
    """Conflict Detection: two tasks in the same slot raise one warning."""
    entries = [
        PlanEntry(time_of_day=TimeOfDay.MORNING, action="Walk Rex", pet_name="Rex"),
        PlanEntry(time_of_day=TimeOfDay.MORNING, action="Walk Mochi", pet_name="Mochi"),
    ]

    warnings = CarePlanner().detect_conflicts(entries)

    assert len(warnings) == 1
    # The warning names the colliding slot and both conflicting parties.
    assert "Morning" in warnings[0]
    assert "Rex" in warnings[0]
    assert "Mochi" in warnings[0]


def test_detect_conflicts_silent_when_slots_are_distinct():
    """Conflict Detection (edge): distinct time slots produce no warnings."""
    entries = [
        PlanEntry(time_of_day=TimeOfDay.MORNING, action="Walk Rex", pet_name="Rex"),
        PlanEntry(time_of_day=TimeOfDay.EVENING, action="Feed Rex", pet_name="Rex"),
    ]

    assert CarePlanner().detect_conflicts(entries) == []


# ---------------------------------------------------------------------------
# Empty / boundary edge cases
# ---------------------------------------------------------------------------
def test_pet_with_no_tasks_yields_empty_plan():
    """Edge case: a pet with no care items produces an empty, well-formed plan."""
    pet = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)

    plan = CarePlanner().generate_daily_plan(pet, date(2026, 7, 6))

    assert plan.to_schedule() == []
    assert "No care tasks" in plan.reasoning


def test_medication_occurs_on_range_boundaries():
    """Edge case: a med course is due on its inclusive start/end, not outside."""
    med = Medication(
        item_id=0,
        time_of_day=TimeOfDay.NIGHT,
        notes="",
        med_name="Carprofen",
        dosage="75mg",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
    )

    assert med.occurs_on(date(2026, 7, 1)) is True   # start (inclusive)
    assert med.occurs_on(date(2026, 7, 31)) is True  # end (inclusive)
    assert med.occurs_on(date(2026, 6, 30)) is False  # day before
    assert med.occurs_on(date(2026, 8, 1)) is False   # day after


if __name__ == "__main__":
    test_mark_complete_changes_task_status()
    test_adding_task_increases_pet_task_count()
    test_schedule_returns_tasks_in_chronological_order()
    test_completing_daily_task_creates_task_for_next_day()
    test_completing_one_off_task_does_not_recur()
    test_completing_daily_task_rolls_over_year_boundary()
    test_detect_conflicts_flags_duplicate_time_slot()
    test_detect_conflicts_silent_when_slots_are_distinct()
    test_pet_with_no_tasks_yields_empty_plan()
    test_medication_occurs_on_range_boundaries()
    print("All tests passed.")
