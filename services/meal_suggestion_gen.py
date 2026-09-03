"""
services/meal_suggestion_gen.py
================================
AI-powered explanations and recipe swaps using the Gemini API.
"""

from typing import Any
from models.food_product import FoodProduct

class MealSuggestionGenerator:
    """Generates AI explanations and healthier-alternative suggestions."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel("gemini-1.5-flash")
            except ImportError:
                self._client = None

    def explain_label(self, product: FoodProduct, nutrition_results: dict[str, Any], fallback_text: str) -> str:
        """
        Returns a plain-language explanation of the product's nutrition.
        Falls back to rule-based summary if API is unavailable or fails.
        """
        if not self._client:
            return fallback_text

        high_items = [k for k, v in nutrition_results.items() if v["high"]]
        prompt = (
            f"Explain simply, in 2-3 friendly sentences for an everyday shopper, "
            f"why the product '{product.name}' might be a concern. "
            f"It is high in: {', '.join(high_items) if high_items else 'nothing in particular'}. "
            f"Avoid technical jargon."
        )
        try:
            response = self._client.generate_content(prompt)
            text = (response.text or "").strip()
            return text if text else fallback_text
        except Exception:
            return fallback_text

    def suggest_alternatives(self, product: FoodProduct, nutrition_results: dict[str, Any]) -> str:
        """
        Suggests healthier food alternatives or a simple recipe idea.
        """
        high_items = [k for k, v in nutrition_results.items() if v["high"]]
        generic_fallback = (
            "Try a version with less added sugar/salt, or pair it with fresh vegetables or fruit to balance the meal."
            if high_items
            else "This product looks fine as part of a balanced diet."
        )
        if not self._client:
            return generic_fallback

        prompt = (
            f"Suggest one healthier alternative product OR one simple homemade "
            f"recipe using similar ingredients to '{product.name}', in 2 sentences max, "
            f"given it is high in: {', '.join(high_items) if high_items else 'nothing in particular'}."
        )
        try:
            response = self._client.generate_content(prompt)
            text = (response.text or "").strip()
            return text if text else generic_fallback
        except Exception:
            return generic_fallback