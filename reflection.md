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

My scheduler considers four constraints, in roughly this order of importance:

1. **Occurrence (is this task even due today?)** — the first thing the planner
   does is ask every care item `occurs_on(day)`. Meals and walks fire on chosen
   weekdays (or every day), medications only within their inclusive start–end
   course, and grooming on one calendar date. A task that isn't due simply never
   enters the plan. This mattered most: a plan full of tasks that don't apply
   today is worse than useless.
2. **Time of day** — surviving tasks are ordered into coarse buckets (morning →
   night) via the `TimeOfDay` `IntEnum`. This is the ordering constraint a pet
   owner actually reasons about, so it's the backbone of the plan.
3. **Priority** — handled at the UI layer, where the app maps a task's priority
   onto a time slot (high → morning, medium → midday, low → evening) so
   higher-priority tasks land earlier in the day.
4. **Completion status** — tracked per entry so the day can be filtered into
   "done" vs. "still to do."

I decided time-of-day and occurrence mattered most because PawPal's job is to
answer "what does my pet need, and roughly when?" — not to be a minute-by-minute
calendar. I deliberately did **not** model precise clock times or owner
preferences beyond priority, because the coarse-bucket granularity is what keeps
the plan readable and the logic simple (see the conflict-detection tradeoff below).

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

I used an AI coding assistant across the whole lifecycle, but for distinct jobs
in each phase: **design brainstorming** to turn the scenario into a first UML
skeleton, **refactoring** to grow that skeleton into working logic, **feature
implementation** for the sorting/filtering/conflict algorithms, **test
generation** for the pytest suite, and **debugging/explanation** when wiring the
backend into Streamlit.

The prompts that worked best were *constraint-first* ones — I told the assistant
what the design must guarantee, not just what to produce. For example, "make the
planner able to select tasks without ever checking an item's concrete type" led
straight to the polymorphic `occurs_on()` / `recurrence()` interface. Prompts
that asked the AI to *justify a tradeoff* ("what breaks if conflict detection only
compares time-of-day buckets?") were far more useful than "write the scheduler,"
because they surfaced the design's limits before I committed to it.

**Most effective assistant features for building the scheduler:** codebase-aware
edits (so a change to `CareItem` propagated cleanly to all four subclasses),
inline generation from the UML skeleton, and the ability to draft an
edge-case-heavy test suite quickly (the year-boundary recurrence and inclusive
medication-date tests came out of asking "what edge cases would this miss?").

**Separate chat sessions per phase kept me organized.** I ran roughly one session
per commit-sized phase — UML/design, core implementation, the Phase 3 algorithms,
tests, and the UI. Keeping them separate meant each session carried only the
context relevant to its job, so the assistant didn't prematurely optimize the data
model while I was still designing it, or drag stale UI assumptions into the
scheduler logic. It also made the work legible after the fact: each session maps
to a clear commit, so I could revisit "why did the medication model change?"
without scrolling through an implementation-and-tests-and-UI mega-thread.

**b. Judgment and verification**

The clearest moment I didn't accept a suggestion as-is: an early version leaned
toward having the planner branch on concrete types (effectively `if isinstance(item,
Medication): ...`) to decide when each kind of task was due. That would have worked,
but it meant the "Brain" had to be edited every time a new care type was added —
exactly the coupling a clean design should avoid. I rejected it and instead pushed
the decision *down into the items themselves* as the abstract `occurs_on(day)` and
`recurrence()` methods, so the planner asks a uniform question and never inspects
subclass types. A related modification: the skeleton modeled medication frequency
as a free-text string ("twice daily"), which code can't act on — I changed it to a
structured `times_per_day` plus a list of `TimeOfDay`s so the scheduler could read
it directly.

I verified suggestions three ways rather than trusting them: I **read** the
generated code against the design invariant it was supposed to uphold (does the
planner still avoid type checks?), I **ran `main.py` end to end** to watch the plan,
sort, filter, recurrence, and conflict output on real objects, and I **wrote an
automated test suite** (10 tests) that pins the behaviors most likely to break
silently — recurrence across a year boundary, inclusive medication start/end dates,
and same-slot vs. distinct-slot conflict detection.

---

## 4. Testing and Verification

**a. What you tested**

The 10-test suite in `test_pawpal.py` targets the core care-planning logic:

- **Sorting** — a day's tasks come back in chronological order (morning → night)
  regardless of insertion order.
- **Recurrence** — completing a *daily* task auto-schedules the next day's
  occurrence, including correctly rolling over a **year boundary**; a *one-off*
  task returns `None` and does not recur.
- **Conflict detection** — two tasks in the same `TimeOfDay` slot produce a
  warning, while tasks in distinct slots stay silent.
- **Care-item management** — adding items to a pet, and marking tasks complete.
- **Occurrence edge cases** — a medication course is due on its **inclusive**
  start and end dates, and a pet with no tasks yields an empty plan.

These behaviors were the important ones to test because they're the parts that
fail *silently*: an off-by-one in the year-boundary date math or an exclusive
instead of inclusive date range would still return a plausible-looking plan, just
a wrong one. The empty-plan and one-off cases guard the "nothing to do" paths that
are easy to forget.

**b. Confidence**

I'm fairly confident the scheduler is correct *for the scenario it models* — coarse
time buckets, per-day planning, simple daily/weekly recurrence — because those paths
are exercised by both the tests and the `main.py` demo. My confidence is lower at
the boundaries the model deliberately doesn't cover.

Edge cases I'd test next with more time:
- **Cross-pet conflicts** — two different pets with a task in the same slot (the
  detector handles it, but the tests focus on single-pet collisions).
- **Weekly recurrence landing on the correct weekday** after a `+7` day advance,
  and interaction with a medication course that ends mid-week.
- **`mark_task_complete` respecting the care item's date range** — right now it
  always spawns a next occurrence even if the underlying course has ended.
- **Shopping-cart quantity inference** for meals bound to specific weekdays vs.
  every day.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the polymorphic `CareItem` design. Because every care type
answers `describe()`, `occurs_on(day)`, and `recurrence()` behind a shared
interface, the `CarePlanner` never inspects concrete types — it just collects,
filters, and orders. That paid off directly: adding grooming appointments and
structured medications didn't require touching the planner at all, and the Phase 3
algorithms (sort, filter, conflict, recurrence) all operate on one uniform
`PlanEntry` list. The clean seam between the stateless planner "Brain" and the
data-holding domain classes is the part of the design I'd keep unchanged.

**b. What you would improve**

If I had another iteration, I'd give tasks **real `HH:MM` times and durations** and
upgrade conflict detection from same-bucket matching to true interval-overlap
checking (the grouping structure is already there to build on). I'd also promote
**priority into a first-class field** on `CareItem` instead of mapping it to a time
slot in the UI, add **persistence** so pets and plans survive an app restart
(everything currently lives in Streamlit session state), and make
`mark_task_complete` **honor the care item's date range** so a finished medication
course stops spawning occurrences.

**c. Key takeaway**

The biggest thing I learned is what it means to be the **lead architect** when the
AI can out-type you. The assistant is extremely fast at producing plausible,
locally-correct code — but "locally correct" and "keeps the system clean" are not
the same thing, and only the human is accountable for the difference. My leverage
came from *owning the invariants and the data model* (e.g., "the planner must never
branch on concrete types") and directing the AI toward them, then verifying its
output against those invariants rather than accepting it because it ran. The AI
generates; the architect decides what the system is *not* allowed to become. Used
that way, the AI made me faster without making the design worse.
