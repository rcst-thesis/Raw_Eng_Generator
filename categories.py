"""
categories.py — user-facing topic categories.

A category is a named bundle of content sources:
    domains   : keys of generator.DOMAINS       (template-driven sentences)
    pools     : keys of generator.POOLS         (ready-made standalone lines)
    dialogue  : keys of generator.DIALOGUE_SECTIONS (question/answer pairs)
    bias      : optional per-strategy weight multipliers

Only strings are stored here, so this module has no import dependency on
generator.py (and therefore no import cycle).

Pick one or many:
    python main.py --category school
    python main.py --category animals,nature,conversation
    python main.py --list-categories
"""

from __future__ import annotations

from dataclasses import dataclass, field

ALL = "all"


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    description: str
    domains: tuple[str, ...] = ()
    pools: tuple[str, ...] = ()
    dialogue: tuple[str, ...] = ()
    bias: dict[str, float] = field(default_factory=dict)


# Bias presets — multipliers applied to the base strategy weights.
_CONVERSATIONAL = {"daily_interaction": 2.0, "dialogue_q": 2.0, "dialogue_a": 2.0,
                   "question": 1.5, "structured": 0.5}
_SIMPLE = {"standalone": 2.0, "daily_interaction": 1.5, "structured": 0.7,
           "compound": 0.3, "conditional": 0.3, "definition": 0.3,
           "aphorism": 0.2, "analogy": 0.2}
_DESCRIPTIVE = {"structured": 1.4, "sensory": 1.5, "narrative": 1.4,
                "comparison": 1.3}


CATEGORIES: dict[str, Category] = {

    # ── Everyday speech ──────────────────────────────────────────────────
    "greetings": Category(
        key="greetings",
        label="Greetings & farewells",
        description="Hellos, goodbyes, introductions, polite openers and closers.",
        domains=("greetings", "farewells"),
        pools=("greetings", "farewells", "introductions", "polite_phrases"),
        dialogue=("greetings_introductions", "farewells"),
        bias=_CONVERSATIONAL,
    ),
    "conversation": Category(
        key="conversation",
        label="Everyday conversation",
        description="Small talk, requests, apologies, thanks, phone calls, plans.",
        domains=("small_talk", "making_requests", "apologies_gratitude",
                 "phone_calls", "communication"),
        pools=("small_talk", "making_requests", "apologies_gratitude",
               "phone_calls", "making_plans", "polite_phrases", "compliments"),
        dialogue=("small_talk", "making_requests", "apologies_gratitude",
                  "phone_calls", "making_plans", "compliments", "communication"),
        bias=_CONVERSATIONAL,
    ),
    "basics": Category(
        key="basics",
        label="Beginner basics",
        description="Very short, high-frequency sentences for absolute beginners.",
        pools=("basics_everyday", "beginner", "child_friendly", "polite_phrases",
               "numbers_time_date"),
        dialogue=("greetings_introductions", "small_talk"),
        bias=_SIMPLE,
    ),
    "emergencies": Category(
        key="emergencies",
        label="Emergencies & help",
        description="Asking for help, accidents, lost items, urgent situations.",
        domains=("healthcare", "making_requests"),
        pools=("emergencies_help", "asking_directions", "polite_phrases"),
        dialogue=("emergencies", "healthcare"),
        bias=_CONVERSATIONAL,
    ),

    # ── People & relationships ───────────────────────────────────────────
    "people": Category(
        key="people",
        label="People & descriptions",
        description="Describing appearance, personality, age, and impressions.",
        domains=("people_description",),
        pools=("people", "introductions"),
        dialogue=("people_relationships",),
        bias=_DESCRIPTIVE,
    ),
    "relationships": Category(
        key="relationships",
        label="Friends & relationships",
        description="Friendship, dating, neighbours, community ties, reconciliation.",
        domains=("relationships", "people_description"),
        pools=("people", "compliments", "expressing_feelings"),
        dialogue=("people_relationships", "compliments"),
    ),
    "family": Category(
        key="family",
        label="Family",
        description="Parents, siblings, relatives, family routines and gatherings.",
        domains=("family", "kids_parenting"),
        pools=("home_life", "kids", "celebrations"),
        dialogue=("family", "kids_parenting"),
    ),
    "kids": Category(
        key="kids",
        label="Children & parenting",
        description="Babies, toddlers, school-age children, parenting talk.",
        domains=("kids_parenting", "family"),
        pools=("kids", "child_friendly"),
        dialogue=("kids_parenting",),
    ),
    "emotions": Category(
        key="emotions",
        label="Feelings & emotions",
        description="Expressing how you feel, reassurance, empathy, mood.",
        domains=("emotions", "mental_health"),
        pools=("expressing_feelings", "compliments"),
        dialogue=("expressing_feelings", "emotions_and_wellbeing", "mental_health"),
    ),

    # ── School & learning ────────────────────────────────────────────────
    "school": Category(
        key="school",
        label="School & education",
        description="Classroom talk, homework, exams, teachers, enrolment.",
        domains=("school", "education_policy"),
        pools=("school_life", "instructional"),
        dialogue=("classroom", "school_life", "education_policy"),
    ),
    "science": Category(
        key="science",
        label="Science",
        description="Experiments, discoveries, research, scientific facts.",
        domains=("science",),
        pools=("science_facts", "advanced"),
        dialogue=("science_and_environment",),
    ),
    "history": Category(
        key="history",
        label="History",
        description="Past events, periods, heritage, historical explanation.",
        domains=("history",),
        pools=("advanced", "intermediate"),
        dialogue=("history",),
    ),
    "philosophy": Category(
        key="philosophy",
        label="Ideas & philosophy",
        description="Abstract reasoning, ethics, reflection, argument.",
        pools=("philosophy", "advanced"),
        bias={"aphorism": 2.0, "reflection": 2.0, "definition": 1.8,
              "rhetorical_question": 1.8, "daily_interaction": 0.2},
    ),

    # ── Nature & living things ───────────────────────────────────────────
    "animals": Category(
        key="animals",
        label="Animals & pets",
        description="Pets, farm animals, wildlife, vets, animal care.",
        domains=("animals",),
        pools=("animals",),
        dialogue=("animals",),
        bias=_DESCRIPTIVE,
    ),
    "nature": Category(
        key="nature",
        label="Nature & landscape",
        description="Rivers, mountains, forests, beaches, seasons, scenery.",
        domains=("nature",),
        pools=("nature",),
        dialogue=("nature",),
        bias=_DESCRIPTIVE,
    ),
    "environment": Category(
        key="environment",
        label="Environment & climate",
        description="Conservation, pollution, climate, sustainability.",
        domains=("environment", "nature"),
        pools=("science_facts", "news"),
        dialogue=("science_and_environment",),
    ),
    "weather": Category(
        key="weather",
        label="Weather & seasons",
        description="Forecasts, storms, heat, rain, seasonal talk.",
        domains=("weather",),
        pools=("nature", "small_talk"),
        dialogue=("weather", "small_talk"),
    ),
    "farming": Category(
        key="farming",
        label="Farming & gardening",
        description="Planting, harvest, soil, livestock, home gardens.",
        domains=("gardening_farming",),
        pools=("gardening_farming",),
        dialogue=("gardening_farming",),
    ),

    # ── Daily living ─────────────────────────────────────────────────────
    "home": Category(
        key="home",
        label="Home & household",
        description="Chores, cooking, repairs, rooms, housemates, bills.",
        domains=("home_life",),
        pools=("home_life", "accommodation"),
        dialogue=("home_life", "accommodation"),
    ),
    "food": Category(
        key="food",
        label="Food & dining",
        description="Cooking, ordering, restaurants, cafés, tastes, recipes.",
        domains=("food", "restaurant_cafe"),
        pools=("restaurant_cafe",),
        dialogue=("food", "restaurant_cafe"),
    ),
    "shopping": Category(
        key="shopping",
        label="Shopping & markets",
        description="Prices, sizes, payment, returns, bargaining, groceries.",
        domains=("shopping",),
        pools=("shopping_phrases",),
        dialogue=("shopping", "shopping_daily"),
    ),
    "clothing": Category(
        key="clothing",
        label="Clothing & fashion",
        description="Sizes, fabrics, tailoring, outfits, dressing for occasions.",
        domains=("clothing_fashion",),
        pools=("clothing",),
        dialogue=("clothing",),
    ),
    "health": Category(
        key="health",
        label="Health & medical",
        description="Symptoms, clinics, appointments, medicine, recovery.",
        domains=("healthcare", "mental_health"),
        pools=("emergencies_help",),
        dialogue=("healthcare", "mental_health"),
    ),
    "fitness": Category(
        key="fitness",
        label="Fitness & exercise",
        description="Workouts, running, gym, recovery, healthy routines.",
        domains=("fitness_exercise", "sport"),
        pools=("fitness",),
        dialogue=("fitness", "sport"),
    ),
    "numbers": Category(
        key="numbers",
        label="Numbers, time & dates",
        description="Telling time, counting, scheduling, dates and durations.",
        pools=("numbers_time_date", "beginner"),
        dialogue=("making_plans",),
        bias=_SIMPLE,
    ),

    # ── Getting around ───────────────────────────────────────────────────
    "travel": Category(
        key="travel",
        label="Travel & tourism",
        description="Trips, hotels, bookings, sightseeing, airports.",
        domains=("travel",),
        pools=("accommodation", "transport_phrases"),
        dialogue=("travel", "accommodation"),
    ),
    "directions": Category(
        key="directions",
        label="Directions & places",
        description="Asking the way, landmarks, distances, getting lost.",
        domains=("asking_directions", "city_places"),
        pools=("asking_directions", "city_places"),
        dialogue=("asking_directions",),
        bias=_CONVERSATIONAL,
    ),
    "transport": Category(
        key="transport",
        label="Transport & commuting",
        description="Buses, jeepneys, trains, fares, traffic, driving.",
        domains=("transport",),
        pools=("transport_phrases",),
        dialogue=("transport", "transport_daily"),
    ),
    "city": Category(
        key="city",
        label="City & community",
        description="Neighbourhoods, public services, local establishments.",
        domains=("city_places", "architecture"),
        pools=("city_places",),
        dialogue=("asking_directions", "architecture"),
    ),

    # ── Work & money ─────────────────────────────────────────────────────
    "work": Category(
        key="work",
        label="Work & workplace",
        description="Meetings, deadlines, colleagues, office routines.",
        domains=("workplace", "jobs_careers"),
        pools=("jobs", "customer_support"),
        dialogue=("workplace", "jobs_careers"),
    ),
    "jobs": Category(
        key="jobs",
        label="Jobs & careers",
        description="Applications, interviews, contracts, career moves.",
        domains=("jobs_careers", "workplace"),
        pools=("jobs",),
        dialogue=("jobs_careers", "workplace"),
    ),
    "business": Category(
        key="business",
        label="Business & selling",
        description="Small business, suppliers, pricing, customers, stock.",
        domains=("business", "finance"),
        pools=("jobs", "customer_support"),
        dialogue=("finance", "shopping"),
    ),
    "money": Category(
        key="money",
        label="Money & finance",
        description="Budgets, savings, bills, loans, banking.",
        domains=("finance", "business"),
        pools=("shopping_phrases", "numbers_time_date"),
        dialogue=("finance", "shopping"),
    ),
    "support": Category(
        key="support",
        label="Customer service",
        description="Support requests, complaints, refunds, service replies.",
        domains=("communication", "shopping"),
        pools=("customer_support", "polite_phrases"),
        dialogue=("shopping", "communication", "phone_calls"),
        bias=_CONVERSATIONAL,
    ),
    "law": Category(
        key="law",
        label="Law & government",
        description="Rules, rights, documents, permits, legal processes.",
        domains=("law", "education_policy"),
        pools=("news", "advanced"),
        dialogue=("law",),
    ),

    # ── Technology & media ───────────────────────────────────────────────
    "technology": Category(
        key="technology",
        label="Technology",
        description="Devices, software, updates, troubleshooting.",
        domains=("technology",),
        pools=("instructional",),
        dialogue=("technology",),
    ),
    "internet": Category(
        key="internet",
        label="Internet & social media",
        description="Online accounts, posts, messaging, connectivity.",
        domains=("internet", "communication"),
        pools=("social_media",),
        dialogue=("internet", "communication"),
    ),
    "gaming": Category(
        key="gaming",
        label="Gaming",
        description="Games, matches, players, in-game talk.",
        domains=("gaming",),
        pools=("social_media",),
        dialogue=("gaming",),
    ),
    "news": Category(
        key="news",
        label="News & current affairs",
        description="Headlines, reports, announcements, public updates.",
        pools=("news", "intermediate"),
        bias={"news_headline": 3.0, "definition": 1.5, "daily_interaction": 0.2},
    ),

    # ── Culture & leisure ────────────────────────────────────────────────
    "culture": Category(
        key="culture",
        label="Culture & traditions",
        description="Customs, language, heritage, community practices.",
        domains=("culture_traditions", "history"),
        pools=("culture",),
        dialogue=("culture_traditions",),
    ),
    "celebrations": Category(
        key="celebrations",
        label="Celebrations & holidays",
        description="Birthdays, weddings, fiestas, reunions, greetings for occasions.",
        domains=("celebrations",),
        pools=("celebrations",),
        dialogue=("celebrations",),
    ),
    "arts": Category(
        key="arts",
        label="Arts & music",
        description="Painting, performance, instruments, concerts, creativity.",
        domains=("arts", "music"),
        pools=("storytelling",),
        dialogue=("arts", "music"),
    ),
    "hobbies": Category(
        key="hobbies",
        label="Hobbies & free time",
        description="Pastimes, crafts, collecting, weekend activities.",
        domains=("hobbies",),
        pools=("storytelling", "intermediate"),
        dialogue=("hobbies",),
    ),
    "sports": Category(
        key="sports",
        label="Sports",
        description="Teams, matches, training, scores, supporters.",
        domains=("sport", "fitness_exercise"),
        pools=("fitness",),
        dialogue=("sport", "fitness"),
    ),
    "stories": Category(
        key="stories",
        label="Stories & narration",
        description="Narrative sentences, anecdotes, scene-setting.",
        pools=("storytelling",),
        bias={"narrative": 3.0, "anecdote_opener": 2.5, "sensory": 2.0,
              "daily_interaction": 0.2},
    ),
}


# ── Convenience groupings ────────────────────────────────────────────────
# A group expands to several categories. Handy shorthands for common mixes.

GROUPS: dict[str, tuple[str, ...]] = {
    "daily": ("greetings", "conversation", "basics", "home", "food", "shopping",
              "directions", "transport", "numbers", "emergencies"),
    "travelpack": ("greetings", "conversation", "travel", "directions",
                   "transport", "food", "shopping", "emergencies", "numbers"),
    "beginner": ("basics", "greetings", "conversation", "numbers", "kids",
                 "school", "home"),
    "academic": ("school", "science", "history", "philosophy", "law", "news"),
    "worklife": ("work", "jobs", "business", "money", "support", "technology"),
    "world": ("animals", "nature", "environment", "weather", "farming", "culture"),
}


# ── Helpers ──────────────────────────────────────────────────────────────

def category_keys() -> list[str]:
    return sorted(CATEGORIES)


def group_keys() -> list[str]:
    return sorted(GROUPS)


def expand(names: list[str] | tuple[str, ...] | None) -> list[str]:
    """
    Normalise a user selection into a concrete list of category keys.

    Accepts category keys, group names, 'all', and comma-separated strings.
    Returns [] for 'all' / None, meaning "use every content source".
    Raises ValueError with a helpful message on an unknown name.
    """
    if not names:
        return []

    flat: list[str] = []
    for raw in names:
        flat.extend(part.strip().lower() for part in str(raw).split(",") if part.strip())

    if ALL in flat:
        return []

    resolved: list[str] = []
    for name in flat:
        if name in GROUPS:
            resolved.extend(k for k in GROUPS[name] if k not in resolved)
        elif name in CATEGORIES:
            if name not in resolved:
                resolved.append(name)
        else:
            raise ValueError(
                f"Unknown category '{name}'.\n"
                f"Categories: {', '.join(category_keys())}\n"
                f"Groups:     {', '.join(group_keys())}\n"
                f"Use 'all' for everything."
            )
    return resolved


def slug(selection: list[str]) -> str:
    """Short filename-safe tag describing a selection."""
    if not selection:
        return "all"
    if len(selection) <= 3:
        return "-".join(selection)
    return f"{selection[0]}-mix{len(selection)}"


def describe_table() -> str:
    """Human-readable listing used by --list-categories."""
    width = max(len(k) for k in CATEGORIES)
    lines = ["Categories:"]
    for key in category_keys():
        cat = CATEGORIES[key]
        lines.append(f"  {key.ljust(width)}  {cat.label} — {cat.description}")
    lines.append("")
    lines.append("Groups (shorthand for several categories):")
    gwidth = max(len(g) for g in GROUPS)
    for key in group_keys():
        lines.append(f"  {key.ljust(gwidth)}  {', '.join(GROUPS[key])}")
    lines.append("")
    lines.append("  all         every category (default)")
    return "\n".join(lines)
