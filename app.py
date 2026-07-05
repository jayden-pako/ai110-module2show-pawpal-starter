from datetime import date

import streamlit as st

from pawpal_system import (
    Owner,
    Pet,
    CarePlanner,
    Walk,
    TimeOfDay,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Persist core objects across reruns -----------------------------------
# Streamlit re-runs this whole script top-to-bottom on every interaction, so a
# plain `owner = Owner(...)` would be recreated empty every click. st.session_state
# is a dict-like "vault" that survives reruns: create the object only if it isn't
# already stored, otherwise reuse the existing one.
if "owner" not in st.session_state:
    st.session_state.owner = Owner.sign_up("Jordan", "jordan@example.com", "changeme")

if "planner" not in st.session_state:
    st.session_state.planner = CarePlanner()

# Convenient local handles (these reference the SAME objects held in the vault).
owner = st.session_state.owner
planner = st.session_state.planner

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+**, your pet-care planning assistant.

Add your pets, schedule their care tasks, then generate a daily plan that's
**sorted** morning-to-night, **filterable** by pet and status, and automatically
**conflict-checked** so overlapping tasks never slip past you.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Add a Pet")

# A form batches its inputs and only reruns the script once, on submit — so the
# pet is created exactly once per click rather than on every keystroke.
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="Calico")
    age = st.number_input("Age (years)", min_value=0.0, max_value=40.0, value=2.0, step=1.0)
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    # `Owner.add_pet` is the method that handles the submitted data. We assign a
    # fresh pet_id from the current pet count, then hand the Pet to the owner.
    new_pet = Pet(
        pet_id=len(owner.pets) + 1,
        pet_name=pet_name,
        animal_type=species,
        pet_breed=breed,
        age=float(age),
    )
    owner.add_pet(new_pet)  # <-- mutates the owner stored in session_state
    st.success(f"Added {pet_name} to {owner.name}'s pets.")

# The UI "updates" simply by re-reading the persisted owner on this rerun.
pets = owner.display_pets()
if pets:
    st.write("Your pets:")
    st.table(
        [
            {"id": p.pet_id, "name": p.pet_name, "species": p.animal_type,
             "breed": p.pet_breed, "age": p.age, "care items": len(p.list_care_items())}
            for p in pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Schedule a Task")
st.caption("Attach a care task (a walk) to one of your pets.")

if not pets:
    st.info("Add a pet first, then you can schedule tasks for it.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_label = st.selectbox(
            "Pet",
            options=pets,
            format_func=lambda p: f"{p.pet_name} ({p.animal_type})",
        )
        task_title = st.text_input("Task title", value="Morning walk")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        add_task = st.form_submit_button("Add task")

    if add_task:
        # Map the UI priority onto a time of day so higher-priority tasks land
        # earlier in the planner's morning->night ordering.
        time_by_priority = {
            "high": TimeOfDay.MORNING,
            "medium": TimeOfDay.MIDDAY,
            "low": TimeOfDay.EVENING,
        }
        walk = Walk(
            item_id=0,  # 0 tells schedule_walk to assign the next id
            time_of_day=time_by_priority[priority],
            notes=task_title,
            duration_minutes=int(duration),
            route="",
            days=[],  # empty => recurs every day
        )
        pet_label.schedule_walk(walk)  # <-- Pet method handles the care item
        st.success(f"Scheduled '{task_title}' for {pet_label.pet_name}.")

st.divider()

st.subheader("Today's Schedule")
st.caption("Builds, sorts, filters, and conflict-checks today's plan across all your pets using CarePlanner.")

# Persist the generated plans in the vault so the filter widgets below can
# re-render the schedule on every rerun without rebuilding it each time.
if st.button("Generate schedule", type="primary"):
    if not owner.display_pets():
        st.warning("Add a pet and at least one task first.")
    else:
        today = date.today()
        st.session_state.plans = planner.generate_daily_plans_for_owner(owner, today)
        st.session_state.plan_date = today

plans = st.session_state.get("plans")
if plans:
    # Flatten every pet's plan into one list so the scheduler can reason across
    # pets — conflicts, sorting, and filtering all operate on the whole day.
    all_entries = [entry for plan in plans.values() for entry in plan.entries]

    # 1) Conflicts FIRST, up top. A pet owner needs to know two tasks clash
    #    *before* reading the table, so we surface them as prominent warnings
    #    that name the pets, the tasks, and the time slot they collide in.
    conflicts = planner.detect_conflicts(all_entries)
    if conflicts:
        st.warning(
            f"⚠️ {len(conflicts)} scheduling conflict(s) found — these tasks land "
            "in the same time slot. Consider moving one to a different part of the day."
        )
        for message in conflicts:
            st.warning(message)
    else:
        st.success("✅ No scheduling conflicts — every task has its own time slot.")

    # 2) Filters, driven by the persisted plan (no rebuild needed).
    pet_options = ["All pets"] + [pet.pet_name for pet in owner.display_pets()]
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        pet_filter = st.selectbox("Show pet", pet_options)
    with filter_col2:
        status_filter = st.selectbox("Show tasks", ["All", "To do", "Completed"])

    # 3) Sort chronologically, then narrow to the chosen pet / status.
    entries = planner.sort_by_time(all_entries)
    if pet_filter != "All pets":
        entries = planner.filter_by_pet(entries, pet_filter)
    if status_filter == "To do":
        entries = planner.filter_by_status(entries, completed=False)
    elif status_filter == "Completed":
        entries = planner.filter_by_status(entries, completed=True)

    # 4) One professional, unified table across all pets.
    if entries:
        st.table(
            [
                {
                    "Time": entry.time_of_day.name.title(),
                    "Pet": entry.pet_name,
                    "Task": entry.action,
                    "Repeats": entry.frequency.value.title(),
                    "Status": "✅ Done" if entry.completed else "⭕ To do",
                }
                for entry in entries
            ]
        )
        st.caption(
            f"Showing {len(entries)} of {len(all_entries)} task(s) "
            f"for {st.session_state.plan_date}."
        )
    else:
        st.info("No tasks match the current filter.")
