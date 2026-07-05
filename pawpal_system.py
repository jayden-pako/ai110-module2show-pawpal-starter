"""PawPal — pet-care planning app.

Class skeleton generated from diagrams/uml.mmd.

Design notes:
- Data-holding objects (Pet, the CareItem family, ShoppingCart, DailyPlan,
  etc.) are modeled as dataclasses to keep them clean and declarative.
- Behavior-heavy classes (Owner authentication, CarePlanner) carry method
  stubs to be implemented later.
- CareItem is an abstract base so meals, meds, walks, and grooming share a
  common shape that the planner can treat uniformly.

Method bodies are intentionally left as stubs (`raise NotImplementedError`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, IntEnum


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


@dataclass
class DateRange:
    """A start/end span, used for a shopping cart's week."""

    start: date
    end: date


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


@dataclass
class Meal(CareItem):
    food_name: str
    portion_grams: float
    days: list[DayOfWeek] = field(default_factory=list)

    def describe(self) -> str:
        raise NotImplementedError

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError


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
        raise NotImplementedError

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError


@dataclass
class Walk(CareItem):
    duration_minutes: int
    route: str
    days: list[DayOfWeek] = field(default_factory=list)

    def describe(self) -> str:
        raise NotImplementedError

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError


@dataclass
class GroomingAppointment(CareItem):
    date_time: datetime
    service_type: str
    provider: str
    confirmed: bool = False

    def describe(self) -> str:
        raise NotImplementedError

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Shopping
# ---------------------------------------------------------------------------
@dataclass
class ShoppingItem:
    product_name: str
    quantity: int
    unit_price: float
    category: str


@dataclass
class ShoppingCart:
    cart_id: int
    week: DateRange
    items: list[ShoppingItem] = field(default_factory=list)

    def add_item(self, item: ShoppingItem) -> None:
        raise NotImplementedError

    def remove_item(self, item_id: int) -> None:
        raise NotImplementedError

    def total(self) -> float:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Daily plan
# ---------------------------------------------------------------------------
@dataclass
class PlanEntry:
    time_of_day: TimeOfDay
    action: str
    care_item: CareItem | None = None
    completed: bool = False


@dataclass
class DailyPlan:
    plan_id: int
    date: date
    reasoning: str = ""
    entries: list[PlanEntry] = field(default_factory=list)

    def add_entry(self, entry: PlanEntry) -> None:
        raise NotImplementedError

    def to_schedule(self) -> list[PlanEntry]:
        raise NotImplementedError


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

    def create_meal(self, food: str, days: list[DayOfWeek]) -> Meal:
        raise NotImplementedError

    def schedule_medication(self, med: Medication) -> Medication:
        raise NotImplementedError

    def schedule_walk(self, walk: Walk) -> None:
        raise NotImplementedError

    def schedule_grooming(self, appointment: GroomingAppointment) -> None:
        raise NotImplementedError

    def build_shopping_cart(self) -> ShoppingCart:
        raise NotImplementedError

    def list_care_items(self) -> list[CareItem]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
@dataclass
class Owner:
    owner_id: int
    name: str
    email: str
    phone_number: str
    _password_hash: str = ""
    pets: list[Pet] = field(default_factory=list)

    @classmethod
    def sign_up(cls, name: str, email: str, password: str) -> "Owner":
        # Constructs a new account, so it is a classmethod rather than an
        # instance method (no Owner exists yet at sign-up time).
        raise NotImplementedError

    def sign_in(self, email: str, password: str) -> bool:
        raise NotImplementedError

    def sign_out(self) -> None:
        raise NotImplementedError

    def set_password(self, new_password: str) -> None:
        raise NotImplementedError

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def remove_pet(self, pet_id: int) -> None:
        raise NotImplementedError

    def display_pets(self) -> list[Pet]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Planner (service)
# ---------------------------------------------------------------------------
class CarePlanner:
    """Reads a pet's care items and produces a reasoned daily plan."""

    def generate_daily_plan(self, pet: Pet, day: date) -> DailyPlan:
        raise NotImplementedError

    def _collect_items_for_day(self, pet: Pet, day: date) -> list[CareItem]:
        raise NotImplementedError

    def _explain_reasoning(self, items: list[CareItem]) -> str:
        raise NotImplementedError
