import re


def _has_price(result: str) -> bool:
    """Check result contains a euro price like 12.500 € or €12,500"""
    return bool(re.search(r"[\d.,]+\s*€|€\s*[\d.,]+", result))


def _has_mileage_and_year(result: str) -> bool:
    """Check result contains a mileage (km) and a 4-digit year"""
    has_km = bool(re.search(r"\d[\d.,]*\s*km", result, re.IGNORECASE))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", result))
    return has_km and has_year


def _has_number(result: str) -> bool:
    """Check result contains at least one number (result count)"""
    return bool(re.search(r"\d+", result))


def _has_dealer_name(result: str) -> bool:
    """Check result contains a plausible dealer/seller name — at least 3 chars, no error keywords."""
    if len(result.strip()) < 3:
        return False
    error_keywords = ["error", "failed", "unable", "could not", "blocked", "not found", "keine"]
    return not any(kw in result.lower() for kw in error_keywords)


TASKS = [
    {
        "id": "cheapest_car",
        "goal": (
            "You are on the AutoScout24 used car search results page, already filtered to cars under 20000 euros sorted by price ascending. "
            "Look at the listings shown and return the make, model, and exact price of the cheapest car (the first listing)."
        ),
        "start_url": "https://www.autoscout24.de/lst?atype=C&cy=D&damaged_listing=exclude&priceto=20000&sort=price&desc=0",
        "success_fn": _has_price,
        "max_steps": 10,
    },
    {
        "id": "first_golf_specs",
        "goal": (
            "You are on the AutoScout24 search results page for VW Golf listings. "
            "Click the first car listing and return its mileage in km and year of first registration."
        ),
        "start_url": "https://www.autoscout24.de/lst/volkswagen/golf?atype=C&cy=D&damaged_listing=exclude&sort=standard",
        "success_fn": _has_mileage_and_year,
        "max_steps": 10,
    },
    {
        "id": "bmw_filter_count",
        "goal": (
            "You are on the AutoScout24 search results page showing BMW cars under 15000 euros. "
            "Find and return the total number of search results shown on the page."
        ),
        "start_url": "https://www.autoscout24.de/lst/bmw?atype=C&cy=D&damaged_listing=exclude&priceto=15000&sort=standard",
        "success_fn": _has_number,
        "max_steps": 8,
    },
    {
        "id": "ui_polo_price_filter",
        "goal": (
            "You are on the AutoScout24 search results page showing VW Polo cars with no price filter applied. "
            "Click on the 'Preis' section in the left filter panel to open the price filter overlay. "
            "Inside the overlay, find the maximum price input field (labeled 'bis' or 'max') and set it to 10000. "
            "Then click the large button at the bottom of the overlay (e.g. 'X Angebote anzeigen') to apply the filter. "
            "If a different overlay opens by mistake, press Escape to close it first. "
            "After returning to the results page, return the total number of results shown (e.g. '2.341 Angebote')."
        ),
        "start_url": "https://www.autoscout24.de/lst/volkswagen/polo?atype=C&cy=D&damaged_listing=exclude",
        "success_fn": _has_number,
        "max_steps": 20,
    },
    {
        "id": "contact_form_fill",
        "goal": (
            "You are on the AutoScout24 VW Golf search results page. "
            "Click the first car listing to open it. "
            "On the listing page, find and click the contact seller button "
            "(labeled 'Verkäufer kontaktieren', 'Händler kontaktieren', or similar). "
            "A contact form will appear. Fill in the following fields:\n"
            "  - Name: Max Mustermann\n"
            "  - Email: test@example.com\n"
            "  - Phone / Telefon: 01701234567\n"
            "  - Message / Nachricht: Ich interessiere mich für dieses Fahrzeug. Ist es noch verfügbar?\n"
            "Do NOT click the send / Senden / Absenden button. "
            "After filling all fields, return the name of the seller or dealership shown on the listing page."
        ),
        "start_url": "https://www.autoscout24.de/lst/volkswagen/golf?atype=C&cy=D&damaged_listing=exclude&sort=standard",
        "success_fn": _has_dealer_name,
        "max_steps": 20,
    },
]
