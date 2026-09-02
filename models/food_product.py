"""
models/food_product.py
=======================
Core data class representing a food product.
"""

from exceptions import IncompleteDataError

class FoodProduct:
    """Represents one food product and its attributes."""

    def __init__(self, barcode: str, name: str, ingredients_text: str = "", nutrients: dict = None, allergens: list = None):
        self.barcode = barcode
        self.name = name
        # Raw ingredient string from API, e.g. "Sugar, Milk, Palm Oil"
        self.ingredients_text = ingredients_text or ""
        # Dictionary of nutrients per 100g, e.g. {"sugars": 12.5, "salt": 1.2}
        self.nutrients = nutrients or {}
        # List of allergen tags, e.g. ["milk", "peanuts"]
        self.allergens = allergens or []

    @classmethod
    def from_api_response(cls, data: dict) -> "FoodProduct":
        """
        Alternate constructor: parses raw JSON response from Open Food Facts
        and extracts only the fields our app cares about.
        """
        product_data = data.get("product")
        if not product_data:
            raise IncompleteDataError("API response did not contain product data.")

        barcode = product_data.get("code", "unknown")
        name = product_data.get("product_name") or product_data.get("product_name_en")
        if not name:
            raise IncompleteDataError(f"Product with barcode {barcode} has no product name in the API data.")

        ingredients_text = product_data.get("ingredients_text", "") or ""
        raw_nutrients = product_data.get("nutriments", {})

        # We pull out the standard 100g nutritional metrics
        nutrients = {
            "energy_kcal": raw_nutrients.get("energy-kcal_100g"),
            "sugars": raw_nutrients.get("sugars_100g"),
            "salt": raw_nutrients.get("salt_100g"),
            "fat": raw_nutrients.get("fat_100g"),
            "saturated_fat": raw_nutrients.get("saturated-fat_100g"),
        }

        return cls(
            barcode=barcode,
            name=name,
            ingredients_text=ingredients_text,
            nutrients=nutrients,
        )

    def to_dict(self) -> dict:
        """Converts the object back into a dictionary for JSON/CSV file saving."""
        return {
            "barcode": self.barcode,
            "name": self.name,
            "ingredients_text": self.ingredients_text,
            "nutrients": self.nutrients,
            "allergens": self.allergens,
        }

    def __repr__(self):
        return f"FoodProduct(barcode={self.barcode!r}, name={self.name!r})"