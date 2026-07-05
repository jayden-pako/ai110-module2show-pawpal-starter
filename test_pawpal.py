"""Tests for the PawPal care-planning algorithm.

Run with pytest:      pytest test_pawpal.py
Or standalone:        python test_pawpal.py
"""

from datetime import date

from pawpal_system import (
    CarePlanner,
    DayOfWeek,
    Owner,
    Pet,
    TimeOfDay,
    Walk,
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


if __name__ == "__main__":
    test_mark_complete_changes_task_status()
    test_adding_task_increases_pet_task_count()
    print("All tests passed.")
