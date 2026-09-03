"""
===================
Regex validation and text sanitization helpers.
"""
import re
from typing import Any
from exceptions import InvalidBarcodeError

# Barcodes (EAN-8, UPC-A, EAN-13, ITF-14) must consist of 8, 12, 13, or 14 numeric digits
BARCODE_PATTERN = re.compile(r"^\d{8}$|^\d{12,14}$")

# Matches numeric integer or decimal values
NUMBER_PATTERN = re.compile(r"[-+]?\d*\.?\d+")


def is_valid_barcode(barcode: str) -> bool:
    """Returns True if the barcode format is valid, otherwise False."""
    if not isinstance(barcode, str):
        return False
    return bool(BARCODE_PATTERN.match(barcode.strip()))


def validate_barcode(barcode: str) -> bool:
    """Validates standard barcodes. Raises InvalidBarcodeError if invalid[cite: 6]."""
    if not is_valid_barcode(barcode):
        raise InvalidBarcodeError(
            f"Invalid barcode format: '{barcode}'. Must be 8, 12, 13, or 14 digits."
        )
    return True


def validate_barcode_or_raise(barcode: str) -> str:
    """Validates barcode format and raises InvalidBarcodeError if invalid."""
    barcode = (barcode or "").strip()
    if not is_valid_barcode(barcode):
        raise InvalidBarcodeError(
            f"'{barcode}' is not a valid barcode. Expected 8, 12, 13, or 14 numeric digits."
        )
    return barcode


def extract_number(value: Any) -> float:
    """
    Extracts the first numeric float from numbers or messy strings.
    Examples:
        extract_number(12.5)      -> 12.5
        extract_number("12.5 g")  -> 12.5
        extract_number("< 1 g")   -> 1.0
        extract_number(None)      -> 0.0
        extract_number("no data") -> 0.0
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = NUMBER_PATTERN.search(str(value))
    if not match:
        return 0.0
    return float(match.group())


# Alias for teammate signature compatibility[cite: 6]
clean_numeric_value = extract_number


def clean_ingredient_text(text: str) -> str:
    """
    Cleans raw ingredients text by stripping parenthetical notes and excess punctuation.
    Example:
        clean_ingredient_text("Sugar (12%),, Milk   , Salt") -> "Sugar, Milk, Salt"
    """
    if not text:
        return ""
    # Remove text in parentheses like "(12%)" or "(from milk)"
    text = re.sub(r"\([^)]*\)", "", text)
    # Collapse double/triple commas into single ones
    text = re.sub(r",\s*,+", ",", text)
    # Remove extra spaces before commas
    text = re.sub(r"\s+,", ",", text)
    # Collapse multiple whitespace characters into a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")