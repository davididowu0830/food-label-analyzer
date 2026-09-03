"""
services/nutrition_analyzer.py
===============================
Analyzes product nutrient values per 100g against health threshold standards.
"""
from typing import Any
from models.food_product import FoodProduct
from utils.validators import extract_number
from exceptions import IncompleteDataError

class NutritionAnalyzer:
    """Analyzes the nutrient values on a FoodProduct and flags concerns."""

    # Standard nutritional thresholds per 100g
    THRESHOLDS = {
        "sugars": 22.5,
        "salt": 1.5,
        "fat": 17.5,
        "saturated_fat": 5.0,
        "energy_kcal": 400.0,
    }

    LABELS = {
        "sugars": "sugar",
        "salt": "salt",
        "fat": "fat",
        "saturated_fat": "saturated fat",
        "energy_kcal": "calories",
    }

    def analyze(self, product: FoodProduct) -> dict[str, Any]:
        """
        Evaluates each nutrient against high thresholds.
        Raises IncompleteDataError if the product has no nutrient data.
        """
        if not product.nutrients or all(v is None for v in product.nutrients.values()):
            raise IncompleteDataError(f"'{product.name}' has no nutrition data available to analyze.")

        results = {}
        for key, threshold in self.THRESHOLDS.items():
            raw_value = product.nutrients.get(key)
            # Uses extract_number regex helper from validators.py
            value = extract_number(raw_value)
            results[key] = {
                "value": value,
                "high": value > threshold,
                "threshold": threshold,
            }
        return results

    def summarize(self, results: dict[str, Any]) -> str:
        """
        Turns the analyzed results into a clean, human-readable sentence.
        This serves as our non-AI fallback summary.
        """
        high_items = [self.LABELS[k] for k, v in results.items() if v["high"]]
        if not high_items:
            return "This product looks reasonably balanced - nothing is flagged as high."
        if len(high_items) == 1:
            joined = high_items[0]
        else:
            joined = ", ".join(high_items[:-1]) + " and " + high_items[-1]
        return f"This product is high in {joined}."