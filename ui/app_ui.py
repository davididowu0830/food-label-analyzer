"""
ui/app_ui.py
============
Streamlit dashboard for Food Label Analyzer.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from services.openfoodfacts_client import OpenFoodFactsClient
from services.nutrition_analyzer import NutritionAnalyzer
from services.allergen_detector import AllergenDetector
from services.meal_suggestion_gen import MealSuggestionGenerator
from storage.food_log_manager import FoodLogManager
from exceptions import (
    InvalidBarcodeError,
    ProductNotFoundError,
    APIRequestError,
    IncompleteDataError,
    FoodLogError,
)

client = OpenFoodFactsClient()
analyzer = NutritionAnalyzer()
allergen_detector = AllergenDetector()
log_manager = FoodLogManager(filepath="food_log.json")

def run_app():
    st.set_page_config(page_title="Food Label Analyzer", page_icon="🥗")
    st.title("🥗 Food Label Analyzer")
    st.write("Enter a product name or barcode to see a plain-English breakdown of its label.")

    if "result" not in st.session_state:
        st.session_state.result = None

    with st.sidebar:
        st.subheader("Settings")
        api_key = st.text_input("Gemini API key (optional)", type="password")
        st.caption("Leave blank to use the built-in rule-based explanations instead of AI.")
        st.divider()
        st.subheader("Your Food Log")
        if st.button("Show saved log"):
            _show_log()

    suggestion_gen = MealSuggestionGenerator(api_key=api_key or None)

    search_mode = st.radio("Search by:", ["Barcode", "Product name"], horizontal=True)
    query = st.text_input("Enter barcode" if search_mode == "Barcode" else "Enter product name")

    if st.button("Analyze"):
        if not query.strip():
            st.warning("Please enter a value first.")
            st.session_state.result = None
        else:
            st.session_state.result = _fetch_and_analyze(query.strip(), search_mode, suggestion_gen)

    if st.session_state.result:
        _render_result(st.session_state.result)

def _fetch_and_analyze(query, search_mode, suggestion_gen):
    try:
        with st.spinner("Looking up product..."):
            if search_mode == "Barcode":
                product = client.get_product_by_barcode(query)
            else:
                product = client.search_by_name(query)

        nutrition_results = analyzer.analyze(product)
        fallback_summary = analyzer.summarize(nutrition_results)
        allergens = allergen_detector.detect(product)
        product.allergens = allergens
        explanation = suggestion_gen.explain_label(product, nutrition_results, fallback_summary)
        suggestion = suggestion_gen.suggest_alternatives(product, nutrition_results)

        return {
            "product": product,
            "nutrition_results": nutrition_results,
            "allergens": allergens,
            "explanation": explanation,
            "suggestion": suggestion,
        }
    except InvalidBarcodeError as e:
        st.error(f"Invalid barcode: {e}")
    except ProductNotFoundError as e:
        st.error(f"Not found: {e}")
    except APIRequestError as e:
        st.error(f"Network problem: {e}")
    except IncompleteDataError as e:
        st.warning(f"Limited data: {e}")
    return None

def _render_result(result):
    product = result["product"]
    nutrition_results = result["nutrition_results"]
    allergens = result["allergens"]

    st.success(f"Found: **{product.name}**")
    st.subheader("Nutrition Breakdown (per 100g)")
    for key, info in nutrition_results.items():
        flag = "🔴 HIGH" if info["high"] else "🟢 OK"
        st.write(f"- **{key.replace('_', ' ').title()}**: {info['value']} (threshold {info['threshold']}) — {flag}")

    st.subheader("Allergens")
    if product.ingredients_text and allergens:
        st.warning("Contains: " + ", ".join(allergens))
    elif product.ingredients_text:
        st.write("No common allergens detected in the ingredient list.")
    else:
        st.info("No ingredient data available to check for allergens.")

    st.subheader("What this means for you")
    st.write(result["explanation"])

    st.subheader("Healthier alternatives / recipe ideas")
    st.write(result["suggestion"])

    if st.button("Save to food log"):
        try:
            log_manager.save_entry(product.to_dict())
            st.success("Saved to your food log!")
        except FoodLogError as e:
            st.error(f"Couldn't save to your food log: {e}")

def _show_log():
    try:
        log = log_manager.load_log()
    except FoodLogError as e:
        st.error(f"Couldn't load food log: {e}")
        return

    if not log:
        st.info("Your food log is empty.")
        return

    st.write(f"{len(log)} saved product(s):")
    for entry in log:
        name = entry.get("name", "Unknown")
        st.write(f"- {name}")