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
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
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

st.subheader("Build Schedule")
st.caption("Generates today's plan for every pet using CarePlanner.")

if st.button("Generate schedule"):
    if not owner.display_pets():
        st.warning("Add a pet and at least one task first.")
    else:
        today = date.today()
        plans = planner.generate_daily_plans_for_owner(owner, today)
        for pet in owner.display_pets():
            plan = plans[pet.pet_id]
            st.markdown(f"**{pet.pet_name}'s plan for {plan.date}**")
            st.caption(plan.reasoning)
            schedule = plan.to_schedule()
            if schedule:
                st.table(
                    [
                        {"time": entry.time_of_day.name.title(), "task": entry.action}
                        for entry in schedule
                    ]
                )
            else:
                st.write("_No tasks scheduled today._")
