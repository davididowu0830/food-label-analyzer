from meal_suggestion_gen import MealSuggestionGenerator

fake_product = {
    "name": "Chocolate Chip Cookies",
    "ingredients": [
        "wheat flour", "sugar", "palm oil", "chocolate chips (sugar, cocoa mass, cocoa butter)",
        "eggs", "baking soda", "salt", "vanilla extract"
    ],
    "nutrients": {
        "calories_per_100g": 480,
        "sugar_g": 32,
        "salt_g": 0.6,
        "fat_g": 22,
    },
    "allergens": ["wheat", "eggs", "milk"],
}

generator = MealSuggestionGenerator()

result = generator.explain_label(fake_product)
print("EXPLAIN LABEL:")
print(result)

alternatives = generator.suggest_alternatives(fake_product)
print("\nSUGGEST ALTERNATIVES:")
print(alternatives)