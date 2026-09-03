import requests

from exceptions import APIRequestError, ProductNotFoundError, InvalidBarcodeError
from models.food_product import FoodProduct
from utils.validators import validate_barcode_or_raise

# Fields we actually use from search hits. ingredients_text is deliberately
# NOT requested here - Open Food Facts stores it as a per-language field
# internally, so it never comes back through search no matter what we ask
# for. search_by_name() works around this by following up with a real
# barcode lookup instead. find_similar_products() only needs these fields.
REQUESTED_FIELDS = "code,product_name,product_name_en,nutriments,categories_tags"


class OpenFoodFactsClient:
    """Wraps all HTTP calls to the Open Food Facts API."""

    BASE_URL = "https://world.openfoodfacts.org/api/v2"
    # Legacy search endpoint - kept here only as a documented reference for
    # why SEARCH_URL below points somewhere else now.
    # OLD_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
    SEARCH_URL = "https://search.openfoodfacts.org/search"
    TIMEOUT_SECONDS = 8
    # Open Food Facts increasingly blocks requests with the default
    # "python-requests/x.x" User-Agent as a basic anti-bot measure (403
    # Forbidden). They ask integrators to identify their app + a contact
    # method, so we do that on every request via a shared session.
    HEADERS = {"User-Agent": "FoodLabelAnalyzer/1.0 (Group 5 student project; contact via GitHub)"}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_product_by_barcode(self, barcode: str) -> FoodProduct:
        """
        Looks up one exact product by barcode.
        Raises:
            InvalidBarcodeError - if the barcode format itself is wrong
            APIRequestError     - if the network/request fails
            ProductNotFoundError- if the API says no such product exists
        """
        barcode = validate_barcode_or_raise(barcode)
        url = f"{self.BASE_URL}/product/{barcode}"

        try:
            response = self.session.get(url, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()  # raises for HTTP 4xx/5xx status codes
        except requests.exceptions.Timeout:
            raise APIRequestError("The request to Open Food Facts timed out. Check your internet connection.")
        except requests.exceptions.ConnectionError:
            raise APIRequestError("Could not connect to Open Food Facts. Are you online?")
        except requests.exceptions.HTTPError as e:
            raise APIRequestError(f"Open Food Facts returned an HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            # Catch-all for any other requests-related failure we didn't
            # anticipated above.
            raise APIRequestError(f"Unexpected network error: {e}")

        try:
            data = response.json()
        except ValueError:
            raise APIRequestError("Open Food Facts returned data that wasn't valid JSON.")

        # The API returns status 0 when the barcode isn't in its database.
        if data.get("status") != 1:
            raise ProductNotFoundError(f"No product found for barcode {barcode}.")

        return FoodProduct.from_api_response(data)

    def search_by_name(self, name: str) -> FoodProduct:
        """
        Searches by product name and returns the FIRST matching result.
        Raises the same exceptions as get_product_by_barcode, except
        InvalidBarcodeError obviously doesn't apply here.

        Uses the Search-a-licious API (search.openfoodfacts.org), which
        replaced the old /cgi/search.pl endpoint, purely to FIND the
        barcode of the best-matching product. We then fetch that barcode
        through get_product_by_barcode() to get the full, authoritative
        record - including ingredients_text.

        Why not just use the search hit directly? Open Food Facts' search
        index stores ingredients_text as a per-language field internally
        (e.g. ingredients_text_en, ingredients_text_fr - it's a "text_lang"
        field, not a single flat string), so a plain `fields=ingredients_text`
        request against search never actually returns it, no matter the
        product. The barcode endpoint doesn't have that problem, so we
        route through it instead of trying to guess the right per-language
        field name.
        """
        if not name or not name.strip():
            raise ProductNotFoundError("Please enter a product name to search.")

        hits = self._search(name.strip(), page_size=1)
        if not hits:
            raise ProductNotFoundError(f"No product found matching '{name}'.")

        barcode = hits[0].get("code")
        if not barcode:
            # Extremely unlikely (every OFF product has a code), but fall
            # back to building straight from the search hit rather than
            # crashing if it ever happens.
            return FoodProduct.from_api_response({"product": hits[0]})

        try:
            return self.get_product_by_barcode(barcode)
        except InvalidBarcodeError:
            # The search index occasionally has a malformed/legacy code
            # that fails our stricter barcode format check. search_by_name
            # is documented not to raise InvalidBarcodeError, so fall back
            # to the (less complete) search hit instead of breaking that
            # contract.
            return FoodProduct.from_api_response({"product": hits[0]})

    def find_similar_products(self, product: FoodProduct, limit: int = 3) -> list:
        """
        Finds other real products in the same category as `product`, for use
        as concrete "healthier alternative" suggestions alongside (or
        instead of) an AI-generated one.

        This is best-effort: if the product has no category data, or the
        request fails, we return an empty list rather than raising - a
        missing "similar products" section shouldn't break the rest of the
        page. Excludes the product itself from the results.
        """
        if not product.categories:
            return []

        # OFF's category tags go broad -> specific (e.g. "beverages",
        # "sodas", "colas"), so the last one is usually the most precise
        # category to search within.
        category = product.categories[-1]

        try:
            hits = self._search(f'categories_tags:"{category}"', page_size=limit + 1)
        except APIRequestError:
            return []

        similar = []
        for hit in hits:
            if hit.get("code") == product.barcode:
                continue  # don't suggest the product itself
            try:
                similar.append(FoodProduct.from_api_response({"product": hit}))
            except Exception:
                continue  # skip any malformed hit rather than failing the whole list
            if len(similar) >= limit:
                break

        return similar

    def _search(self, query: str, page_size: int = 1) -> list:
        """Shared helper for hitting the Search-a-licious /search endpoint."""
        params = {
            "q": query,
            "page_size": page_size,
            "fields": REQUESTED_FIELDS,
        }

        try:
            response = self.session.get(self.SEARCH_URL, params=params, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise APIRequestError("The request to Open Food Facts timed out.")
        except requests.exceptions.ConnectionError:
            raise APIRequestError("Could not connect to Open Food Facts. Are you online?")
        except requests.exceptions.HTTPError as e:
            raise APIRequestError(f"Open Food Facts returned an HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Unexpected network error: {e}")

        try:
            data = response.json()
        except ValueError:
            raise APIRequestError("Open Food Facts returned data that wasn't valid JSON.")

        return data.get("hits", [])
