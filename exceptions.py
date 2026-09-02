"""
exceptions.py
=============
Every custom error the app can raise lives here in ONE place.
"""

class FoodAnalyzerError(Exception):
    """Base class for every error raised by this application."""
    pass


class InvalidBarcodeError(FoodAnalyzerError):
    """Raised when a barcode string fails regex validation (wrong format/length)."""
    pass


class ProductNotFoundError(FoodAnalyzerError):
    """Raised when the API responds successfully but has no matching product."""
    pass


class APIRequestError(FoodAnalyzerError):
    """Raised when the network request fails (timeout, no internet, bad status code)."""
    pass


class IncompleteDataError(FoodAnalyzerError):
    """Raised when a product is found, but is missing required data (like nutrition facts)."""
    pass


class FoodLogError(FoodAnalyzerError):
    """Raised when saving or loading the food log file fails."""
    pass