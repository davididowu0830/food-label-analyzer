"""
=============================
Scans ingredient lists for common allergen keywords using regex word boundaries.
"""
import re
from typing import Any, List, Dict
from utils.validators import clean_ingredient_text


class AllergenDetector:
    """Detects common allergens by keyword-matching cleaned ingredient text."""

    ALLERGEN_KEYWORDS = {
        "milk": ["milk", "lactose", "whey", "casein", "butter", "cream", "cheese", "ghee"],
        "eggs": ["egg", "eggs", "albumin", "globulin", "livetin", "mayonnaise"],
        "peanuts": ["peanut", "peanuts", "groundnut", "arachis"],
        "tree nuts": ["almond", "cashew", "walnut", "hazelnut", "pistachio", "pecan", "macadamia", "brazil nut"],
        "soy": ["soy", "soya", "soybean", "lecithin", "tofu", "edamame"],
        "wheat/gluten": ["wheat", "gluten", "barley", "rye", "flour", "spelt", "kamut", "triticale"],
        "fish": ["fish", "anchovy", "cod", "salmon", "tuna", "halibut", "mackerel"],
        "shellfish": ["shrimp", "prawn", "crab", "lobster", "shellfish", "crustacean", "mollusk", "clam", "mussel", "oyster"],
        "sesame": ["sesame", "tahini"],
    }

    def detect_allergens(self, ingredients_text: str) -> List[str]:
        """Scans an ingredient string and returns detected categories."""
        text = clean_ingredient_text(ingredients_text).lower()
        if not text:
            return []

        found = []
        for allergen, keywords in self.ALLERGEN_KEYWORDS.items():
            for keyword in keywords:
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, text):
                    found.append(allergen)
                    break
        return found

    def detect(self, product_or_text: Any) -> List[str]:
        """Polymorphic entry point accepting either a FoodProduct instance or a raw string."""
        if hasattr(product_or_text, "ingredients_text"):
            text = product_or_text.ingredients_text
        else:
            text = str(product_or_text or "")
        return self.detect_allergens(text)

    def generate_allergen_report(self, ingredients_text: str) -> Dict[str, Any]:
        """Provides a structured dictionary report indicating presence and specific items found."""
        found = self.detect_allergens(ingredients_text)
        return {
            "has_allergens": len(found) > 0,
            "detected_allergens": found,
        }