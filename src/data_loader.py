"""Data loader module for parsing item JSON files."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ItemDatabase:
    """Manages loading and querying item data."""

    def __init__(self, data_dir: Path):
        """
        Initialize the item database.

        Args:
            data_dir: Path to the Data directory
        """
        self.data_dir = Path(data_dir)
        self.items_dir = self.data_dir / "Items"
        self.items: Dict[str, dict] = {}
        self.reverse_recipes: Dict[str, List[str]] = {}  # material_id -> [item_ids that use it]

    def load_all_items(self):
        """Load all item JSON files from the Items directory."""
        if not self.items_dir.exists():
            raise FileNotFoundError(f"Items directory not found: {self.items_dir}")

        # Load all JSON files
        for json_file in self.items_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    item_data = json.load(f)
                    item_id = item_data.get('id')

                    if item_id:
                        self.items[item_id] = item_data
                    else:
                        print(f"Warning: Item in {json_file.name} has no 'id' field")

            except json.JSONDecodeError as e:
                print(f"Error parsing {json_file.name}: {e}")
            except Exception as e:
                print(f"Error loading {json_file.name}: {e}")

        # Build reverse recipe mapping
        self._build_reverse_recipes()

    def _build_reverse_recipes(self):
        """Build a mapping of materials to items that use them in recipes."""
        self.reverse_recipes = {}

        for item_id, item_data in self.items.items():
            recipe = item_data.get('recipe', {})

            for material_id in recipe.keys():
                if material_id not in self.reverse_recipes:
                    self.reverse_recipes[material_id] = []
                self.reverse_recipes[material_id].append(item_id)

    def get_item(self, item_id: str) -> Optional[dict]:
        """
        Get item data by ID.

        Args:
            item_id: The item's unique identifier

        Returns:
            Item data dictionary or None if not found
        """
        return self.items.get(item_id)

    def get_items_using_material(self, material_id: str) -> List[dict]:
        """
        Get all items that use the given material in their recipe.

        Args:
            material_id: The material's item ID

        Returns:
            List of item data dictionaries
        """
        item_ids = self.reverse_recipes.get(material_id, [])
        return [self.items[item_id] for item_id in item_ids if item_id in self.items]

    def search_by_name(self, name: str, language: str = 'en') -> List[dict]:
        """
        Search items by name (case-insensitive).

        Args:
            name: The name to search for
            language: Language code for the name

        Returns:
            List of matching item data dictionaries
        """
        name_lower = name.lower()
        results = []

        for item_data in self.items.values():
            item_name = item_data.get('name', {}).get(language, '')
            if name_lower in item_name.lower():
                results.append(item_data)

        return results
