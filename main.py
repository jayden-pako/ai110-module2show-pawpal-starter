"""PawPal demo — build an owner with pets, schedule tasks, print today's plan.

Run:  python main.py
"""

from datetime import date, datetime

from pawpal_system import (
    CarePlanner,
    GroomingAppointment,
    Meal,
    Medication,
    Owner,
    Pet,
    TimeOfDay,
    Walk,
)


def main() -> None:
    today = date.today()

    # 1. Create an owner (sign up + sign in).
    owner = Owner.sign_up("Jayden", "business@jaydenpako.com", "hunter2")
    owner.sign_in("business@jaydenpako.com", "hunter2")

    # 2. Create at least two pets and register them with the owner.
    rex = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)
    mochi = Pet(pet_id=2, pet_name="Mochi", animal_type="Cat", pet_breed="Calico", age=2)
    owner.add_pet(rex)
    owner.add_pet(mochi)

    # 3. Add at least three tasks at different times of day.
    #    (empty `days` list => scheduled every day, so they land on `today`.)
    rex.meals.append(
        Meal(
            item_id=0,
            time_of_day=TimeOfDay.MORNING,
            notes="one scoop",
            food_name="Kibble",
            portion_grams=150.0,
            days=[],
        )
    )
    rex.schedule_walk(
        Walk(
            item_id=0,
            time_of_day=TimeOfDay.AFTERNOON,
            notes="keep it on-leash",
            duration_minutes=30,
            route="Riverside loop",
            days=[],
        )
    )
    rex.schedule_grooming(
        GroomingAppointment(
            item_id=0,
            time_of_day=TimeOfDay.MIDDAY,
            notes="nail trim too",
            date_time=datetime(today.year, today.month, today.day, 12, 30),
            service_type="Bath & brush",
            provider="Happy Paws",
            confirmed=True,
        )
    )
    # Deliberately schedule a second MORNING task for Rex so the conflict
    # detector has something to catch (his breakfast is also in the morning).
    rex.schedule_medication(
        Medication(
            item_id=0,
            time_of_day=TimeOfDay.MORNING,
            notes="give with breakfast",
            med_name="Heartgard",
            dosage="1 chew",
            start_date=today,
            end_date=today,
            times_per_day=1,
        )
    )

    mochi.meals.append(
        Meal(
            item_id=0,
            time_of_day=TimeOfDay.EVENING,
            notes="",
            food_name="Wet food",
            portion_grams=85.0,
            days=[],
        )
    )
    mochi.schedule_medication(
        Medication(
            item_id=0,
            time_of_day=TimeOfDay.NIGHT,
            notes="with food",
            med_name="Amitriptyline",
            dosage="5mg",
            start_date=today,
            end_date=today,
            times_per_day=1,
        )
    )

    # 4. Ask the planner to build today's plan for every pet and print it.
    planner = CarePlanner()
    plans = planner.generate_daily_plans_for_owner(owner, today)

    print("=" * 44)
    print(f"Today's Schedule — {today:%A, %B %d, %Y}")
    print(f"Owner: {owner.name}")
    print("=" * 44)

    for pet in owner.display_pets():
        plan = plans[pet.pet_id]
        print(f"\n{pet.pet_name} ({pet.animal_type})")
        schedule = plan.to_schedule()
        if not schedule:
            print("  Nothing scheduled today.")
        for entry in schedule:
            print(f"  [{entry.time_of_day.name:<9}] {entry.action}")

    # 5. Exercise the new scheduling algorithms on a flat list of every task.
    #    Collect the entries in whatever order the pets/plans yield them (i.e.
    #    NOT pre-sorted) so sort_by_time() has real work to do.
    all_entries = [
        entry
        for pet in owner.display_pets()
        for entry in plans[pet.pet_id].entries
    ]

    print("\n" + "=" * 44)
    print("All tasks sorted by time of day")
    print("=" * 44)
    for entry in planner.sort_by_time(all_entries):
        print(f"  [{entry.time_of_day.name:<9}] {entry.pet_name}: {entry.action}")

    # -- Filtering by pet --------------------------------------------------
    rex_entries = planner.filter_by_pet(all_entries, "Rex")
    print(f"\nFilter by pet — Rex has {len(rex_entries)} task(s) today.")

    # -- Recurrence: complete a daily task and auto-schedule the next one ---
    breakfast = planner.filter_by_pet(all_entries, "Rex")[0]
    next_occurrence = planner.mark_task_complete(breakfast)
    print(
        f"\nCompleted '{breakfast.action}' "
        f"(frequency: {breakfast.frequency.name})."
    )
    if next_occurrence is not None:
        print(
            f"  -> auto-scheduled next occurrence for "
            f"{next_occurrence.due_date:%A, %b %d}."
        )

    # -- Filtering by status (after completing one task) -------------------
    done = planner.filter_by_status(all_entries, completed=True)
    pending = planner.filter_by_status(all_entries, completed=False)
    print(
        f"\nFilter by status — {len(done)} done, {len(pending)} pending."
    )

    # -- Conflict detection ------------------------------------------------
    print("\n" + "=" * 44)
    print("Conflict check")
    print("=" * 44)
    conflicts = planner.detect_conflicts(all_entries)
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts found.")


if __name__ == "__main__":
    main()
