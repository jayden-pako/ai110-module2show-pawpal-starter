"""PawPal — pet-care planning app.

Class skeleton generated from diagrams/uml.mmd, now with working behavior.

Design notes:
- Data-holding objects (Pet, the CareItem family, ShoppingCart, DailyPlan,
  etc.) are modeled as dataclasses to keep them clean and declarative.
- Behavior-heavy classes (Owner authentication, CarePlanner) carry the real
  logic that drives the system.
- CareItem is an abstract base so meals, meds, walks, and grooming share a
  common shape that the planner can treat uniformly. Every concrete item
  answers two questions polymorphically: `describe()` (what am I?) and
  `occurs_on(day)` (am I due on this date?).

Communication map (who talks to whom):

    CarePlanner ── reads ──▶ Owner.display_pets()
         │                        │
         │                        ▼
         └── per pet ──▶ Pet.list_care_items() ──▶ [CareItem, ...]
                                 │
                                 ▼  (planner asks each item)
                    CareItem.occurs_on(day) / CareItem.describe()
                                 │
                                 ▼
                    PlanEntry ──collected into──▶ DailyPlan
                                 │
                                 ▼
                    DailyPlan stored back on Pet.plans

The planner never inspects concrete subclass types; it relies entirely on the
CareItem interface, so new care kinds slot in without changing the Brain.
"""

from __future__ import annotations

import hashlib
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum, IntEnum
from itertools import count


# ---------------------------------------------------------------------------
# Value types / enums
# ---------------------------------------------------------------------------
class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class TimeOfDay(IntEnum):
    # IntEnum so plan entries can be sorted chronologically (morning -> night).
    MORNING = 1
    MIDDAY = 2
    AFTERNOON = 3
    EVENING = 4
    NIGHT = 5


class Frequency(Enum):
    """How often a care item repeats."""

    NONE = "none"      # a one-off (e.g. a single grooming appointment)
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class DateRange:
    """A start/end span, used for a shopping cart's week."""

    start: date
    end: date

    def contains(self, day: date) -> bool:
        """Return True if `day` falls within this span (inclusive)."""
        return self.start <= day <= self.end


# Weekday order matches date.weekday() (0 = Monday ... 6 = Sunday), which is the
# same order the DayOfWeek members are declared in, so an index lookup is exact.
_WEEKDAYS: list[DayOfWeek] = list(DayOfWeek)


def _day_of_week(day: date) -> DayOfWeek:
    """Map a calendar date onto its DayOfWeek member."""
    return _WEEKDAYS[day.weekday()]


def _current_week(today: date | None = None) -> DateRange:
    """Return the Monday..Sunday span containing `today` (defaults to now)."""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    return DateRange(start=monday, end=monday + timedelta(days=6))


# ---------------------------------------------------------------------------
# Care items (abstract base + concrete kinds)
# ---------------------------------------------------------------------------
@dataclass
class CareItem(ABC):
    """Anything scheduled for a pet on a given part of the day."""

    item_id: int
    time_of_day: TimeOfDay
    notes: str

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable summary of this care item."""
        raise NotImplementedError

    @abstractmethod
    def occurs_on(self, day: date) -> bool:
        """Return True if this care item is scheduled on the given day.

        Lets the planner select items polymorphically without inspecting
        concrete subclass types.
        """
        raise NotImplementedError

    def _with_notes(self, text: str) -> str:
        """Append notes to a description if any are present."""
        return f"{text} — {self.notes}" if self.notes else text

    def recurrence(self) -> Frequency:
        """Return how often this item repeats (default: a one-off).

        Polymorphic like describe()/occurs_on(): the scheduler asks any item how
        often it recurs without inspecting concrete subclass types.
        """
        return Frequency.NONE


@dataclass
class Meal(CareItem):
    food_name: str
    portion_grams: float
    days: list[DayOfWeek] = field(default_factory=list)

    def describe(self) -> str:
        summary = (
            f"Meal: {self.portion_grams:g}g of {self.food_name} "
            f"({self.time_of_day.name.title()})"
        )
        return self._with_notes(summary)

    def occurs_on(self, day: date) -> bool:
        # An empty day list means "every day" (e.g. a standing daily feeding).
        return not self.days or _day_of_week(day) in self.days

    def recurrence(self) -> Frequency:
        """Return how often this meal repeats.

        No specific weekdays means a standing daily feeding; a non-empty `days`
        list means it recurs weekly on those days.
        """
        return Frequency.DAILY if not self.days else Frequency.WEEKLY


@dataclass
class Medication(CareItem):
    med_name: str
    dosage: str
    start_date: date
    end_date: date
    # Structured frequency so the scheduler can read it directly, rather than a
    # free-form string like "twice daily".
    times_per_day: int = 1
    times_of_day: list[TimeOfDay] = field(default_factory=list)

    def describe(self) -> str:
        summary = (
            f"Medication: {self.med_name} {self.dosage}, "
            f"{self.times_per_day}x/day"
        )
        return self._with_notes(summary)

    def occurs_on(self, day: date) -> bool:
        # A course of medication runs across an inclusive date range.
        return self.start_date <= day <= self.end_date

    def recurrence(self) -> Frequency:
        """Return how often this medication repeats.

        A medication is taken on every day its course is active, so it always
        recurs daily (the course's date range bounds when it actually applies).
        """
        return Frequency.DAILY


@dataclass
class Walk(CareItem):
    duration_minutes: int
    route: str
    days: list[DayOfWeek] = field(default_factory=list)

    def describe(self) -> str:
        summary = (
            f"Walk: {self.duration_minutes} min via {self.route} "
            f"({self.time_of_day.name.title()})"
        )
        return self._with_notes(summary)

    def occurs_on(self, day: date) -> bool:
        return not self.days or _day_of_week(day) in self.days

    def recurrence(self) -> Frequency:
        """Return how often this walk repeats.

        No specific weekdays means a standing daily walk; a non-empty `days`
        list means it recurs weekly on those days.
        """
        return Frequency.DAILY if not self.days else Frequency.WEEKLY


@dataclass
class GroomingAppointment(CareItem):
    date_time: datetime
    service_type: str
    provider: str
    confirmed: bool = False

    def describe(self) -> str:
        status = "confirmed" if self.confirmed else "unconfirmed"
        summary = (
            f"Grooming: {self.service_type} with {self.provider} "
            f"at {self.date_time:%Y-%m-%d %H:%M} ({status})"
        )
        return self._with_notes(summary)

    def occurs_on(self, day: date) -> bool:
        # A one-off appointment happens on exactly one calendar day.
        return self.date_time.date() == day


# ---------------------------------------------------------------------------
# Shopping
# ---------------------------------------------------------------------------
@dataclass
class ShoppingItem:
    product_name: str
    quantity: int
    unit_price: float
    category: str

    def line_total(self) -> float:
        """Return the cost of this line (quantity times unit price)."""
        return self.quantity * self.unit_price


@dataclass
class ShoppingCart:
    cart_id: int
    week: DateRange
    items: list[ShoppingItem] = field(default_factory=list)

    def add_item(self, item: ShoppingItem) -> None:
        """Append a shopping item to the cart."""
        self.items.append(item)

    def remove_item(self, item_id: int) -> None:
        """Remove the item at position `item_id` if it exists."""
        # ShoppingItem carries no id of its own, so `item_id` is the item's
        # zero-based position in the cart (the order it was added).
        if 0 <= item_id < len(self.items):
            del self.items[item_id]

    def total(self) -> float:
        """Return the summed cost of every item in the cart."""
        return sum(item.line_total() for item in self.items)


# ---------------------------------------------------------------------------
# Daily plan
# ---------------------------------------------------------------------------
@dataclass
class PlanEntry:
    time_of_day: TimeOfDay
    action: str
    care_item: CareItem | None = None
    completed: bool = False
    # Denormalized fields the scheduler reads after a plan is built: which pet
    # owns the task (for filtering / conflict messages), how often it repeats,
    # and the date it is due (so completing a recurring task can spawn the next).
    pet_name: str = ""
    frequency: Frequency = Frequency.NONE
    due_date: date | None = None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


@dataclass
class DailyPlan:
    plan_id: int
    date: date
    reasoning: str = ""
    entries: list[PlanEntry] = field(default_factory=list)

    def add_entry(self, entry: PlanEntry) -> None:
        """Append a plan entry to this day's list of tasks."""
        self.entries.append(entry)

    def to_schedule(self) -> list[PlanEntry]:
        """Return the day's entries ordered chronologically."""
        # Present the day in chronological order (morning -> night).
        return sorted(self.entries, key=lambda e: e.time_of_day)


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------
@dataclass
class Pet:
    pet_id: int
    pet_name: str
    animal_type: str
    pet_breed: str
    age: float
    owner: "Owner | None" = None
    meals: list[Meal] = field(default_factory=list)
    medications: list[Medication] = field(default_factory=list)
    walks: list[Walk] = field(default_factory=list)
    grooming: list[GroomingAppointment] = field(default_factory=list)
    # One cart per week; kept as a list so prior weeks are retained.
    shopping_carts: list[ShoppingCart] = field(default_factory=list)
    plans: list[DailyPlan] = field(default_factory=list)

    def _next_item_id(self) -> int:
        """Return the next unused care-item id for this pet."""
        existing = [item.item_id for item in self.list_care_items()]
        return max(existing, default=0) + 1

    def create_meal(self, food: str, days: list[DayOfWeek]) -> Meal:
        """Create, attach, and return a Meal for the given food and days."""
        meal = Meal(
            item_id=self._next_item_id(),
            time_of_day=TimeOfDay.MORNING,
            notes="",
            food_name=food,
            portion_grams=0.0,
            days=list(days),
        )
        self.meals.append(meal)
        return meal

    def schedule_medication(self, med: Medication) -> Medication:
        """Attach a medication to this pet, assigning an id if needed."""
        if med.item_id == 0:
            med.item_id = self._next_item_id()
        self.medications.append(med)
        return med

    def schedule_walk(self, walk: Walk) -> None:
        """Attach a walk to this pet, assigning an id if needed."""
        if walk.item_id == 0:
            walk.item_id = self._next_item_id()
        self.walks.append(walk)

    def schedule_grooming(self, appointment: GroomingAppointment) -> None:
        """Attach a grooming appointment to this pet, assigning an id if needed."""
        if appointment.item_id == 0:
            appointment.item_id = self._next_item_id()
        self.grooming.append(appointment)

    def build_shopping_cart(self) -> ShoppingCart:
        """Derive a weekly cart from this pet's recurring care items.

        Prices aren't known here, so unit_price is left at 0.0 for the owner to
        fill in; quantities are inferred from how often each item recurs.
        """
        week = _current_week()
        cart = ShoppingCart(cart_id=len(self.shopping_carts) + 1, week=week)

        for meal in self.meals:
            # One portion per scheduled day (a bare list => every day of week).
            servings = len(meal.days) or 7
            cart.add_item(
                ShoppingItem(
                    product_name=meal.food_name,
                    quantity=servings,
                    unit_price=0.0,
                    category="Food",
                )
            )

        for med in self.medications:
            # Only stock meds whose course overlaps this week.
            if med.end_date >= week.start and med.start_date <= week.end:
                cart.add_item(
                    ShoppingItem(
                        product_name=med.med_name,
                        quantity=med.times_per_day * 7,
                        unit_price=0.0,
                        category="Medication",
                    )
                )

        self.shopping_carts.append(cart)
        return cart

    def list_care_items(self) -> list[CareItem]:
        """The single retrieval surface the planner reads from.

        Flattens every care category into one uniform list of CareItem so
        callers never touch the concrete-typed collections directly.
        """
        items: list[CareItem] = []
        items.extend(self.meals)
        items.extend(self.medications)
        items.extend(self.walks)
        items.extend(self.grooming)
        return items


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
_owner_id_seq = count(1)


def _hash_password(password: str, salt: str | None = None) -> str:
    """Return a `salt$digest` string using PBKDF2-HMAC-SHA256."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    ).hex()
    return f"{salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    """Return True if `password` matches the stored `salt$digest` string."""
    if "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    return secrets.compare_digest(_hash_password(password, salt), stored)


@dataclass
class Owner:
    owner_id: int
    name: str
    email: str
    phone_number: str
    _password_hash: str = ""
    pets: list[Pet] = field(default_factory=list)
    _signed_in: bool = False

    @classmethod
    def sign_up(cls, name: str, email: str, password: str) -> "Owner":
        """Create and return a new Owner account with the given credentials."""
        # Constructs a new account, so it is a classmethod rather than an
        # instance method (no Owner exists yet at sign-up time).
        owner = cls(
            owner_id=next(_owner_id_seq),
            name=name,
            email=email,
            phone_number="",
        )
        owner.set_password(password)
        return owner

    def sign_in(self, email: str, password: str) -> bool:
        """Authenticate the owner; return True and mark signed in on success."""
        if email == self.email and _verify_password(password, self._password_hash):
            self._signed_in = True
            return True
        return False

    def sign_out(self) -> None:
        """Mark the owner as signed out."""
        self._signed_in = False

    def set_password(self, new_password: str) -> None:
        """Hash and store a new password for the owner."""
        self._password_hash = _hash_password(new_password)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner and set its back-reference."""
        pet.owner = self  # keep the back-reference in sync
        self.pets.append(pet)

    def remove_pet(self, pet_id: int) -> None:
        """Remove the pet with the given id from this owner."""
        self.pets = [pet for pet in self.pets if pet.pet_id != pet_id]

    def display_pets(self) -> list[Pet]:
        """Return a copy of this owner's list of pets."""
        return list(self.pets)


# ---------------------------------------------------------------------------
# Planner (service) — the "Brain"
# ---------------------------------------------------------------------------
class CarePlanner:
    """Reads a pet's care items and produces a reasoned daily plan.

    The planner is stateless: it holds no data of its own, it orchestrates the
    data classes. It retrieves tasks (Pet.list_care_items), organizes them
    (filter by occurs_on, order by TimeOfDay), and manages the output as a
    DailyPlan stored back on the pet.
    """

    def __init__(self) -> None:
        """Initialize the planner with a fresh plan-id sequence."""
        self._plan_id_seq = count(1)

    # -- single pet -------------------------------------------------------
    def generate_daily_plan(self, pet: Pet, day: date) -> DailyPlan:
        """Build, store, and return one pet's ordered plan for the given day."""
        items = self._collect_items_for_day(pet, day)
        plan = DailyPlan(plan_id=next(self._plan_id_seq), date=day)

        for item in sorted(items, key=lambda i: i.time_of_day):
            plan.add_entry(
                PlanEntry(
                    time_of_day=item.time_of_day,
                    action=item.describe(),
                    care_item=item,
                    pet_name=pet.pet_name,
                    frequency=item.recurrence(),
                    due_date=day,
                )
            )

        plan.reasoning = self._explain_reasoning(items)
        pet.plans.append(plan)  # hand the finished plan back to the pet
        return plan

    # -- across every pet an owner has ------------------------------------
    def generate_daily_plans_for_owner(
        self, owner: Owner, day: date
    ) -> dict[int, DailyPlan]:
        """Retrieve and plan tasks across ALL of an owner's pets for a day.

        This is the top-level entry point: the planner walks the owner's pets
        and builds one DailyPlan each, keyed by pet_id.
        """
        return {
            pet.pet_id: self.generate_daily_plan(pet, day)
            for pet in owner.display_pets()
        }

    # -- internals --------------------------------------------------------
    def _collect_items_for_day(self, pet: Pet, day: date) -> list[CareItem]:
        """Return the pet's care items that are due on the given day."""
        # Ask the pet for everything, then let each item decide if it's due.
        return [item for item in pet.list_care_items() if item.occurs_on(day)]

    def _explain_reasoning(self, items: list[CareItem]) -> str:
        """Return a short summary of the plan's task counts by kind."""
        if not items:
            return "No care tasks are scheduled for this day."

        counts: dict[str, int] = {}
        for item in items:
            kind = type(item).__name__
            counts[kind] = counts.get(kind, 0) + 1

        breakdown = ", ".join(
            f"{count} {kind.lower()}{'s' if count != 1 else ''}"
            for kind, count in sorted(counts.items())
        )
        return (
            f"{len(items)} task(s) planned ({breakdown}), "
            "ordered from morning to night."
        )

    # -- sorting / filtering ----------------------------------------------
    def sort_by_time(self, entries: list[PlanEntry]) -> list[PlanEntry]:
        """Return plan entries ordered from morning to night.

        `time_of_day` is an IntEnum, so a single lambda key sorts them
        chronologically. (If times were stored as "HH:MM" strings instead, the
        same `key=lambda e: e.time` would still sort correctly, because
        zero-padded clock strings sort lexicographically — "08:30" < "12:00".)
        """
        return sorted(entries, key=lambda entry: entry.time_of_day)

    def filter_by_status(
        self, entries: list[PlanEntry], completed: bool
    ) -> list[PlanEntry]:
        """Return only the entries whose completion matches `completed`."""
        return [entry for entry in entries if entry.completed == completed]

    def filter_by_pet(
        self, entries: list[PlanEntry], pet_name: str
    ) -> list[PlanEntry]:
        """Return only the entries belonging to the named pet (case-insensitive)."""
        target = pet_name.strip().lower()
        return [entry for entry in entries if entry.pet_name.lower() == target]

    # -- recurrence -------------------------------------------------------
    def mark_task_complete(self, entry: PlanEntry) -> PlanEntry | None:
        """Mark a task done and, if it recurs, return its next occurrence.

        Uses timedelta to advance the due date accurately: +1 day for DAILY,
        +7 days for WEEKLY. One-off tasks return None (nothing to reschedule).
        """
        entry.mark_complete()

        step_days = {Frequency.DAILY: 1, Frequency.WEEKLY: 7}.get(entry.frequency)
        if step_days is None or entry.due_date is None:
            return None  # one-off, or no due date to advance from

        return PlanEntry(
            time_of_day=entry.time_of_day,
            action=entry.action,
            care_item=entry.care_item,
            completed=False,  # the fresh occurrence starts incomplete
            pet_name=entry.pet_name,
            frequency=entry.frequency,
            due_date=entry.due_date + timedelta(days=step_days),
        )

    # -- conflict detection -----------------------------------------------
    def detect_conflicts(self, entries: list[PlanEntry]) -> list[str]:
        """Return a warning string per time slot that holds more than one task.

        Lightweight by design: it flags exact same-slot collisions (across all
        pets) and returns human-readable strings instead of raising, so callers
        can print the warnings and keep running.
        """
        by_slot: dict[TimeOfDay, list[PlanEntry]] = {}
        for entry in entries:
            by_slot.setdefault(entry.time_of_day, []).append(entry)

        warnings: list[str] = []
        for slot in sorted(by_slot):
            group = by_slot[slot]
            if len(group) > 1:
                who = "; ".join(
                    f"{entry.pet_name or 'unknown'} — {entry.action}"
                    for entry in group
                )
                warnings.append(
                    f"Conflict at {slot.name.title()}: {len(group)} tasks "
                    f"overlap ({who})."
                )
        return warnings


# ---------------------------------------------------------------------------
# Demonstration of the classes communicating end-to-end
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. An owner signs up and authenticates.
    owner = Owner.sign_up("Alex", "alex@example.com", "hunter2")
    assert owner.sign_in("alex@example.com", "hunter2")

    # 2. The owner registers pets.
    rex = Pet(pet_id=1, pet_name="Rex", animal_type="Dog", pet_breed="Lab", age=4)
    mochi = Pet(pet_id=2, pet_name="Mochi", animal_type="Cat", pet_breed="Calico", age=2)
    owner.add_pet(rex)
    owner.add_pet(mochi)

    # 3. Care items are attached to the pets (each object owns its own data).
    rex.create_meal("Kibble", [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY])
    rex.schedule_walk(
        Walk(
            item_id=0,
            time_of_day=TimeOfDay.EVENING,
            notes="park loop",
            duration_minutes=30,
            route="Riverside",
            days=[DayOfWeek.MONDAY],
        )
    )
    rex.schedule_medication(
        Medication(
            item_id=0,
            time_of_day=TimeOfDay.NIGHT,
            notes="with food",
            med_name="Carprofen",
            dosage="75mg",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            times_per_day=1,
        )
    )
    mochi.create_meal("Wet food", [])  # every day

    # 4. The Brain retrieves tasks across ALL the owner's pets for a given day.
    planner = CarePlanner()
    a_monday = date(2026, 7, 6)
    plans = planner.generate_daily_plans_for_owner(owner, a_monday)

    for pet in owner.display_pets():
        plan = plans[pet.pet_id]
        print(f"\n{pet.pet_name}'s plan for {plan.date} — {plan.reasoning}")
        for entry in plan.to_schedule():
            print(f"  [{entry.time_of_day.name:<9}] {entry.action}")

    # 5. Shopping carts are derived from recurring care items.
    cart = rex.build_shopping_cart()
    print(f"\nRex's cart for week {cart.week.start}..{cart.week.end}:")
    for item in cart.items:
        print(f"  {item.quantity}x {item.product_name} ({item.category})")
