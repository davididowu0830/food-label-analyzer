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

        if client is not None:
            self._client = client
            return

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise MealSuggestionError(
                "GEMINI_API_KEY is not configured in the environment or .env file."
            )
        if genai is None:
            raise MealSuggestionError(
                "The google-genai package is required to use Gemini."
            )

        try:
            self._client = genai.Client(api_key=key)
        except Exception as exc:
            raise MealSuggestionError("Unable to initialize the Gemini client.") from exc

    def explain_label(self, product: Any) -> dict[str, Any]:
        payload = self._request_json(product, "explain_label")
        summary = payload.get("summary")
        flags = payload.get("flags")
        if not isinstance(summary, str) or not isinstance(flags, list):
            return self._fallback("explain_label")
        return {"summary": summary, "flags": [str(flag) for flag in flags]}

    def suggest_alternatives(self, product: Any) -> list[dict[str, str]]:
        payload = self._request_json(product, "suggest_alternatives")
        alternatives = payload.get("alternatives")
        if not isinstance(alternatives, list):
            return self._fallback("suggest_alternatives")["alternatives"]

        result = []
        for alternative in alternatives:
            if not isinstance(alternative, Mapping):
                return self._fallback("suggest_alternatives")["alternatives"]
            name = alternative.get("name")
            reason = alternative.get("reason")
            if not isinstance(name, str) or not isinstance(reason, str):
                return self._fallback("suggest_alternatives")["alternatives"]
            result.append({"name": name, "reason": reason})
        return result

    def _request_json(self, product: Any, task: str) -> dict[str, Any]:
        prompt = self._build_prompt(product, task)

        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                return self._parse_json(response.text)
            except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
                prompt = (
                    f"{prompt}\n\nYour previous response was invalid. Return only valid JSON."
                )
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
                    "name": "A comparable lower-sugar, lower-salt recipe",
                    "reason": "Use the same main ingredients with less added sugar and salt.",
                }
            ]
        }

    def _build_prompt(self, product: Any, task: str) -> str:
        product_data = self._product_to_dict(product)
        if task == "explain_label":
            output = '{"summary": "...", "flags": ["high_sugar"]}'
            instruction = (
                "Explain in plain language whether the sugar, salt, fat, and calories "
                "appear high. Use flags only from high_sugar, high_sodium, high_fat, "
                "and high_calories."
            )
        elif task == "suggest_alternatives":
            output = '{"alternatives": [{"name": "...", "reason": "..."}]}'
            instruction = (
                "Suggest 2 or 3 healthier alternatives or similar recipes using "
                "comparable ingredients."
            )
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
            product = product.to_dict()
        if isinstance(product, Mapping):
            return dict(product)
        raise TypeError("product must be a mapping or provide a to_dict() method")

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