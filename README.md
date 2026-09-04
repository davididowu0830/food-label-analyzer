# 🥗 Food Label Analyzer

An intelligent, modular Python application designed to help everyday consumers decode complex food product labels into clear, actionable health insights. By fetching product records from the Open Food Facts worldwide database, the application flags high-risk nutritional metrics (sugars, salts, and saturated fats), detects hidden allergens using regex pattern matching, offers AI-powered dietary recommendations via Google Gemini, and logs food history locally.

---

## 👥 Project Team & Responsibilities (Group 5)

| Team Member | Assigned Layer / Module | Key Responsibilities |
| :--- | :--- | :--- |
| **David Idowu** | `ui/app_ui.py`<br>`main.py`<br>`models/food product.py`<br>`exceptions.py` | Team Lead, Project Architecture, Streamlit Dashboard & State Management, Pipeline Integration |
| **King Akara-Nwaogu** | `services/openfoodfacts_client.py` | Open Food Facts HTTP API integration, Search-a-licious routing, network error handling |
| **Olumide Adeleye** | `services/nutrition_analyzer.py` | Per-100g nutrient threshold evaluation, health concern flagging, rule-based fallback summaries |
| **Delight James** | `services/allergen_detector.py`<br>`utils/validators.py` | Barcode/number regex validation, text sanitization, and keyword-boundary allergen detection |
| **Emmanuel John** | `services/meal_suggestion_gen.py` | Gemini 1.5 Flash API prompt engineering, healthy recipe swaps, graceful offline degradation |
| **Nasiteh Kpanja** | `storage/food_log_manager.py` | Local history persistence, defensive file I/O handling, and JSON/CSV serialization |

---

## 🏗️ System Architecture & Modularity

The application strictly adheres to Object-Oriented Programming (OOP) principles, Separation of Concerns (SoC), and defensive software design:

```text
food-label-analyzer/
├── models/
│   ├── __init__.py
│   └── food_product.py          # Encapsulated data model and API factory deserializer
├── services/
│   ├── __init__.py
│   ├── allergen_detector.py     # Regex word-boundary allergen scanner
│   ├── meal_suggestion_gen.py   # AI integration via Google Generative AI (Gemini)
│   ├── nutrition_analyzer.py    # Health standard nutrient threshold analysis
│   └── openfoodfacts_client.py  # HTTP client wrapper with bot-prevention headers
├── storage/
│   ├── __init__.py
│   └── food_log_manager.py      # JSON and CSV persistence engine
├── ui/
│   ├── __init__.py
│   └── app_ui.py                # Streamlit reactive user interface
├── utils/
│   ├── __init__.py
│   └── validators.py            # Input validation and regex sanitizers
├── .gitignore                   # Ignores __pycache__, virtual environments, and data files
├── exceptions.py                # Centralized hierarchy of domain-specific exceptions


├── main.py                      # Clean application entry point
├── README.md                    # Project documentation and developer guide
└── requirements.txt             # External dependencies
