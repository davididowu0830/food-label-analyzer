"""
storage/food_log_manager.py
============================
Owner: Nasiteh Kpanja

Saves and loads the user's "food log" - the list of products they've
scanned - to a file on disk. Supports both JSON and CSV, chosen by the
file extension. This is the module most focused on File Handling and
Exception Handling from the Python-concepts checklist.
"""

import json
import csv
import os

from exceptions import FoodLogError


class FoodLogManager:
    """Handles reading and writing the food log file (JSON or CSV)."""

    def __init__(self, filepath: str = "food_log.json"):
        self.filepath = filepath

    def _is_csv(self) -> bool:
        return self.filepath.lower().endswith(".csv")

    def save_entry(self, entry: dict) -> None:
        """
        Appends one entry (a plain dict, e.g. product.to_dict()) to the log
        file. Creates the file if it doesn't exist yet.
        Raises FoodLogError on any failure (permission denied, disk full,
        corrupted existing file, etc.) instead of letting a raw
        exception bubble up to the UI.
        """
        try:
            if self._is_csv():
                self._save_entry_csv(entry)
            else:
                self._save_entry_json(entry)
        except PermissionError:
            raise FoodLogError(f"Permission denied writing to '{self.filepath}'.")
        except OSError as e:
            raise FoodLogError(f"Could not write to '{self.filepath}': {e}")

    def _save_entry_json(self, entry: dict) -> None:
        log = self.load_log()  # load_log already handles "file doesn't exist yet"
        log.append(entry)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)

    def _save_entry_csv(self, entry: dict) -> None:
        file_exists = os.path.isfile(self.filepath)
        # Flatten nested fields (nutrients, allergens) into simple strings so
        # they fit neatly into CSV columns.
        flat_entry = {
            "barcode": entry.get("barcode", ""),
            "name": entry.get("name", ""),
            "allergens": ", ".join(entry.get("allergens", [])),
            "sugars": entry.get("nutrients", {}).get("sugars", ""),
            "salt": entry.get("nutrients", {}).get("salt", ""),
            "fat": entry.get("nutrients", {}).get("fat", ""),
            "energy_kcal": entry.get("nutrients", {}).get("energy_kcal", ""),
        }
        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=flat_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(flat_entry)

    def load_log(self) -> list:
        """
        Returns the full log as a list of dicts. Returns an empty list if
        the file doesn't exist yet (that's a normal "first run", not an
        error). Raises FoodLogError if the file exists but is corrupted/
        unreadable.
        """
        if not os.path.isfile(self.filepath):
            return []

        try:
            if self._is_csv():
                with open(self.filepath, "r", newline="", encoding="utf-8") as f:
                    return list(csv.DictReader(f))
            else:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    return json.loads(content)
        except json.JSONDecodeError:
            raise FoodLogError(
                f"'{self.filepath}' exists but contains invalid JSON and can't be read."
            )
        except PermissionError:
            raise FoodLogError(f"Permission denied reading '{self.filepath}'.")
        except OSError as e:
            raise FoodLogError(f"Could not read '{self.filepath}': {e}")
