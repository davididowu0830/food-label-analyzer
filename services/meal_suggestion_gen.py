"""Gemini-backed food label explanations and healthier alternatives."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[assignment]


class MealSuggestionError(RuntimeError):
    """Raised when Gemini cannot produce a meal suggestion response."""


class MealSuggestionGenerator:
    """Generate structured food-label explanations and alternatives with Gemini."""

    def __init__(
        self,
        client: Any | None = None,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        load_dotenv()
        self._model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self._client = None

        if client is not None:
            self._client = client
            return

        key = api_key or os.getenv("GEMINI_API_KEY")
        if key and genai is not None:
            try:
                self._client = genai.Client(api_key=key)
            except Exception:
                self._client = None

    def explain_label(self, product: Any, nutrition_results: Any = None, fallback_summary: str = "") -> str:
        """Explains the nutritional label using Gemini or falls back to rule-based summary."""
        if not self._client:
            return fallback_summary or "The label could not be analyzed with AI (no API key configured)."

        try:
            payload = self._request_json(product, "explain_label")
            summary = payload.get("summary")
            if isinstance(summary, str) and summary.strip():
                return summary
        except Exception:
            pass

        return fallback_summary or self._fallback("explain_label")["summary"]

    def suggest_alternatives(self, product: Any, nutrition_results: Any = None) -> str:
        """Suggests healthier alternatives using Gemini or returns fallback advice."""
        if not self._client:
            return "Consider choosing whole, unprocessed alternatives with lower sodium, sugar, and saturated fat."

        try:
            payload = self._request_json(product, "suggest_alternatives")
            alternatives = payload.get("alternatives")
            if isinstance(alternatives, list) and alternatives:
                formatted = []
                for alt in alternatives:
                    if isinstance(alt, Mapping):
                        name = alt.get("name", "Alternative")
                        reason = alt.get("reason", "")
                        formatted.append(f"• **{name}**: {reason}")
                if formatted:
                    return "\n\n".join(formatted)
        except Exception:
            pass

        return "Consider choosing whole, unprocessed alternatives with lower sodium, sugar, and saturated fat."

    def _request_json(self, product: Any, task: str) -> dict[str, Any]:
        prompt = self._build_prompt(product, task)

        for _ in range(2):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                return self._parse_json(response.text)
            except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
                prompt = f"{prompt}\n\nYour previous response was invalid. Return only valid JSON."
            except Exception as exc:
                raise MealSuggestionError("Gemini request failed.") from exc

        return self._fallback(task)

    @staticmethod
    def _fallback(task: str) -> dict[str, Any]:
        if task == "explain_label":
            return {
                "summary": "The label could not be analyzed right now.",
                "flags": [],
            }
        return {
            "alternatives": [
                {
                    "name": "A comparable lower-sugar, lower-salt alternative",
                    "reason": "Uses whole ingredients with less added sodium and sugar.",
                }
            ]
        }

    def _build_prompt(self, product: Any, task: str) -> str:
        product_data = self._product_to_dict(product)
        if task == "explain_label":
            output = '{"summary": "...", "flags": ["high_sugar"]}'
            instruction = (
                "Explain in plain language whether the sugar, salt, fat, and calories "
                "appear high. Use flags only from high_sugar, high_sodium, high_fat, and high_calories."
            )
        elif task == "suggest_alternatives":
            output = '{"alternatives": [{"name": "...", "reason": "..."}]}'
            instruction = "Suggest 2 or 3 healthier alternatives or recipes using comparable ingredients."
        else:
            raise ValueError(f"Unsupported meal suggestion task: {task}")

        return (
            "You are a helpful nutrition assistant. Use only the food data provided. "
            "Do not diagnose medical conditions. "
            f"{instruction} Return JSON only in this shape: {output}\n\n"
            f"Food product data:\n{json.dumps(product_data, ensure_ascii=True, default=str)}"
        )

    @staticmethod
    def _product_to_dict(product: Any) -> dict[str, Any]:
        if hasattr(product, "to_dict"):
            return product.to_dict()
        if isinstance(product, Mapping):
            return dict(product)
        return {
            "name": getattr(product, "name", "Unknown"),
            "barcode": getattr(product, "barcode", ""),
            "nutriments": getattr(product, "nutriments", {}),
            "ingredients_text": getattr(product, "ingredients_text", ""),
        }

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        if not isinstance(text, str):
            raise TypeError("Gemini response text must be a string")
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Gemini response must be a JSON object")
        return parsed