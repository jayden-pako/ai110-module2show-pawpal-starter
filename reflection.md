# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design models PawPal as an owner who manages pets, where each pet
has scheduled care items. The
key design decision was to promote the app's core actions (add meal, schedule
meds, schedule a walk, schedule grooming) into first-class objects rather than
leaving them as methods on `Pet`, so each has its own state and lifecycle.

- **Owner** — Represents a user account. Responsible for authentication
  (`sign_up`, `sign_in`, `sign_out`, `set_password`) and managing its pets
  (`add_pet`, `remove_pet`, `display_pets`). Stores the password as a private
  `_password_hash` rather than plaintext.
- **Pet** — The central domain entity (name, animal type, breed, age). Owns its
  collections of care items (meals, medications, walks, grooming appointments),
  its weekly shopping cart, and its generated plans. Provides factory/scheduling
  methods (`create_meal`, `schedule_medication`, `schedule_walk`,
  `schedule_grooming`, `build_shopping_cart`, `list_care_items`).
- **CareItem (abstract base)** — Defines the common shape shared by everything
  scheduled for a pet: `item_id`, `time_of_day`, `notes`, and an abstract
  `describe()`. This lets the planner treat every care type uniformly.
- **Meal, Medication, Walk, GroomingAppointment** — Concrete care items that
  inherit from `CareItem`, each adding its own fields (e.g. `food_name`/`days`
  for meals, `dosage`/`frequency` for medications). Responsible for representing
  one specific kind of scheduled care.
- **ShoppingCart** — Represents one pet's weekly shopping for a `DateRange`.
  Responsible for holding `ShoppingItem`s and computing the `total()`.
- **ShoppingItem** — A single line item (product, quantity, unit price,
  category).
- **DailyPlan** — The generated plan for a specific date. Responsible for
  holding the ordered `PlanEntry`s and the `reasoning` string that explains why
  the plan was built that way.
- **PlanEntry** — One time-slotted action within a plan, optionally linked back
  to the `CareItem` it came from and tracking whether it's `completed`.
- **CarePlanner** — A stateless service class. Responsible for the scheduling
  logic: it reads a pet's care items for a given day, orders them, and produces
  a `DailyPlan` with reasoning (`generate_daily_plan`, plus the private helpers
  `_collect_items_for_day` and `_explain_reasoning`).

Supporting value types `DayOfWeek` and `TimeOfDay` (enums) and `DateRange`
provide type safety for fields that would otherwise be loose strings.

**b. Design changes**

Yes. After reviewing the first skeleton, I made several changes so the scheduler
would actually be able to do its job. Here is what I changed and why:

- **Added an `occurs_on(day)` method to every care item.** Meals, meds, walks,
  and grooming each store their timing differently. Without a shared method, the
  planner would have to check the type of each item one by one. Now it can just
  ask any item "are you happening on this day?" and get an answer, no matter what
  kind of item it is.

- **Gave medications a clear frequency instead of plain text.** Before, the
  frequency was just a string like "twice daily," which the code can't really
  understand. I changed it to a number (`times_per_day`) plus a list of times of
  day, so the scheduler can read it directly.

- **Made `TimeOfDay` sortable.** The plan needs to list things in order from
  morning to night. The original version couldn't be sorted, so I switched it to
  use numbers (morning = 1, night = 5). Now ordering the day just works.

- **Linked each pet back to its owner.** The owner had a list of pets, but a pet
  had no way to know who owned it. I added an `owner` field to `Pet` so the
  relationship goes both ways and a pet can't get separated from its owner.

- **Turned sign-up into a method that creates the account.** Sign-up was written
  as something you call on an existing owner, but that doesn't make sense because
  the owner doesn't exist yet. I changed it to a classmethod that builds and
  returns a new owner.

- **Allowed a pet to keep more than one shopping cart.** A pet had a single cart,
  but carts are weekly, so the old design erased last week's cart every time. I
  changed it to a list of carts so past weeks are kept.

I made these changes because the original design looked fine on the surface but
would have blocked the scheduler from being written cleanly. Fixing the data
model first was cheaper than working around it later.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

One deliberate tradeoff is that conflict detection only flags tasks that share
the *exact* same `TimeOfDay` slot (e.g. two MORNING tasks), instead of reasoning
about real clock times and overlapping durations. A 30-minute walk at 8:00 and a
vet call at 8:15 would **not** be flagged, because both are simply "MORNING."

This is reasonable for PawPal's scenario. The planner organizes a pet owner's day
into coarse buckets (morning → night) rather than a minute-by-minute calendar, so
"two things in the same part of the day" is exactly the granularity an owner
actually cares about. Keeping it to exact-slot matching means `detect_conflicts`
stays O(n), returns a friendly warning string instead of crashing, and never has
to invent precise start/end times the data model doesn't store. If the app later
adds real HH:MM times and durations, the same grouping structure can be upgraded
to interval-overlap checking without changing any of its callers.

A related tradeoff: when a recurring task is completed, `mark_task_complete`
spawns the next occurrence by advancing the due date with `timedelta` (+1 day for
daily, +7 for weekly) but does not re-verify the underlying care item's own date
range. This favors a simple, predictable "always produce the next instance" rule
over perfectly modeling, say, a medication course that ends mid-week.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
