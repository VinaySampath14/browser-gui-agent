"""
Hard / adversarial tasks designed to stress-test the agent.
These are intentionally harder than the baseline tasks in definitions.py.
"""

import re


def _has_price(result: str) -> bool:
    return bool(re.search(r"[\d.,]+\s*€|€\s*[\d.,]+", result))

def _has_mileage_and_year(result: str) -> bool:
    has_km = bool(re.search(r"\d[\d.,]*\s*km", result, re.IGNORECASE))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", result))
    return has_km and has_year

def _has_number(result: str) -> bool:
    return bool(re.search(r"\d+", result))

def _has_make_and_model(result: str) -> bool:
    words = result.strip().split()
    return len(words) >= 2

def _has_fuel_type(result: str) -> bool:
    fuels = ["benzin", "diesel", "elektro", "hybrid", "petrol", "electric", "gasoline"]
    return any(f in result.lower() for f in fuels)


HARD_TASKS = [
    # --- Tier 1: Same site, harder navigation ---
    {
        "id": "hard_sort_by_mileage",
        "goal": (
            "You are on the AutoScout24 used car search page. "
            "Change the sort order to sort by mileage ascending (lowest km first). "
            "Return the make, model, and mileage of the first result after sorting."
        ),
        "start_url": "https://www.autoscout24.de/lst?atype=C&cy=D&damaged_listing=exclude&sort=standard",
        "success_fn": _has_mileage_and_year,
        "max_steps": 12,
        "expected_failure": None,
    },
    {
        "id": "hard_specific_year_filter",
        "goal": (
            "You are on the AutoScout24 search page. "
            "Filter results to show only cars registered between 2020 and 2023. "
            "Return the make, model, and year of the first result."
        ),
        "start_url": "https://www.autoscout24.de/lst?atype=C&cy=D&damaged_listing=exclude",
        "success_fn": _has_mileage_and_year,
        "max_steps": 12,
        "expected_failure": None,
    },
    {
        "id": "hard_listing_fuel_type",
        "goal": (
            "You are on the AutoScout24 VW Golf search results page. "
            "Open the first listing. "
            "Return the fuel type of the car (e.g. Diesel, Benzin, Elektro)."
        ),
        "start_url": "https://www.autoscout24.de/lst/volkswagen/golf?atype=C&cy=D&damaged_listing=exclude",
        "success_fn": _has_fuel_type,
        "max_steps": 10,
        "expected_failure": None,
    },

    # --- Tier 2: Different site (mobile.de — known to block) ---
    {
        "id": "mobile_de_blocked",
        "goal": (
            "Go to https://www.mobile.de and find the cheapest used car under 10000 euros. "
            "Return the make, model, and price."
        ),
        "start_url": "https://www.mobile.de",
        "success_fn": _has_price,
        "max_steps": 15,
        "expected_failure": "IP blocked by Cloudflare bot protection",
    },

    # --- Tier 3: Multi-step form interaction ---
    {
        "id": "hard_multi_filter",
        "goal": (
            "You are on the AutoScout24 search page. "
            "Apply ALL of these filters: make=Audi, max price=25000, fuel type=Diesel. "
            "Return the number of results shown after all filters are applied."
        ),
        "start_url": "https://www.autoscout24.de/lst?atype=C&cy=D&damaged_listing=exclude",
        "success_fn": _has_number,
        "max_steps": 15,
        "expected_failure": None,
    },

    # --- Tier 4: Ambiguous / open-ended ---
    {
        "id": "hard_compare_two_listings",
        "goal": (
            "You are on the AutoScout24 BMW search results page under 15000 euros. "
            "Look at the first two listings. "
            "Return which one has lower mileage and what that mileage is."
        ),
        "start_url": "https://www.autoscout24.de/lst/bmw?atype=C&cy=D&damaged_listing=exclude&priceto=15000",
        "success_fn": _has_mileage_and_year,
        "max_steps": 12,
        "expected_failure": None,
    },
]
