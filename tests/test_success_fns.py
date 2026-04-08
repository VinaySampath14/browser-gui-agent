"""
Tests for task success functions in tasks/definitions.py
These are pure functions — no browser or API calls needed.
"""
import pytest
from tasks.definitions import (
    _has_price,
    _has_mileage_and_year,
    _has_number,
    _has_dealer_name,
)


# --- _has_price ---

class TestHasPrice:
    def test_euro_suffix(self):
        assert _has_price("VW Golf, 12.500 €")

    def test_euro_prefix(self):
        assert _has_price("Price: €9,999")

    def test_compact_format(self):
        assert _has_price("8500€")

    def test_no_price(self):
        assert not _has_price("VW Golf, great condition")

    def test_empty_string(self):
        assert not _has_price("")

    def test_number_without_euro(self):
        assert not _has_price("12500 dollars")


# --- _has_mileage_and_year ---

class TestHasMileageAndYear:
    def test_both_present(self):
        assert _has_mileage_and_year("85.000 km, 2019")

    def test_mileage_uppercase(self):
        assert _has_mileage_and_year("120000 KM, registered 2021")

    def test_missing_year(self):
        assert not _has_mileage_and_year("85.000 km, good condition")

    def test_missing_mileage(self):
        assert not _has_mileage_and_year("Year: 2020, excellent shape")

    def test_neither(self):
        assert not _has_mileage_and_year("VW Golf available now")

    def test_year_boundary_valid(self):
        assert _has_mileage_and_year("50000 km, 2000")

    def test_year_boundary_invalid(self):
        assert not _has_mileage_and_year("50000 km, 1899")


# --- _has_number ---

class TestHasNumber:
    def test_plain_number(self):
        assert _has_number("1234 results found")

    def test_single_digit(self):
        assert _has_number("3 Angebote")

    def test_no_number(self):
        assert not _has_number("No results found")

    def test_empty(self):
        assert not _has_number("")

    def test_number_in_word(self):
        assert _has_number("42")


# --- _has_dealer_name ---

class TestHasDealerName:
    def test_normal_dealer_name(self):
        assert _has_dealer_name("Autohaus Müller GmbH")

    def test_simple_name(self):
        assert _has_dealer_name("Max Mustermann")

    def test_too_short(self):
        assert not _has_dealer_name("AB")

    def test_empty(self):
        assert not _has_dealer_name("")

    def test_whitespace_only(self):
        assert not _has_dealer_name("   ")

    def test_error_keyword_blocked(self):
        assert not _has_dealer_name("Error: could not load dealer info")

    def test_failed_keyword(self):
        assert not _has_dealer_name("Failed to find seller")

    def test_unable_keyword(self):
        assert not _has_dealer_name("Unable to contact dealer")

    def test_german_error_keyword(self):
        assert not _has_dealer_name("Keine Ergebnisse gefunden")
