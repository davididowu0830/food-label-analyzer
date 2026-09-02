
 
import os
import sys
 
# Allow this file to import modules from the project root when run directly
# via `streamlit run ui/app_ui.py`.
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
 
# --- one instance of each service, created once per app run ---
client = OpenFoodFactsClient()
analyzer = NutritionAnalyzer()
allergen_detector = AllergenDetector()
log_manager = FoodLogManager(filepath="food_log.json")
 
 
def run_app():
    st.set_page_config(page_title="Food Label Analyzer", page_icon="🥫")
    st.title("🥫 Food Label Analyzer")
    st.write("Enter a product name or barcode to see a plain-English breakdown of its label.")
 
    # Streamlit reruns this whole script on every click (Analyze, Save, etc).
    # If we only ever computed the result inside "if st.button('Analyze')",
    # then clicking any OTHER button (like Save) would rerun the script with
    # Analyze reporting False, so the result section - Save button included -
    # would vanish before the click could register. Stashing the result in
    # st.session_state means it survives reruns triggered by other buttons.
    if "result" not in st.session_state:
        st.session_state.result = None
 
    # Gemini API key is optional - the app still works without it.
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
 
    # Render from session_state (not from the Analyze click) so the result,
    # and its Save button, stay on screen across reruns.
    if st.session_state.result:
        _render_result(st.session_state.result)
 
 
def _fetch_and_analyze(query, search_mode, suggestion_gen):
    """Runs the full pipeline: fetch -> analyze -> detect allergens -> explain.
    Returns a dict of everything _render_result() needs, or None if a
    handled error occurred (the error message is already shown here)."""
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
    """Displays an already-fetched result and the Save button. Called every
    rerun as long as st.session_state.result is set, so the Save button
    keeps working no matter which button triggered the rerun."""
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
 
    # --- Save to log ---
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
 
 
if __name__ == "__main__":
    run_app()