"""Data loader module for parsing item JSON files."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ItemDatabase:
    """Manages loading and querying item + hideout bench data."""

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

        # Hideout benches (workstations) data
        self.hideout_dir = self.data_dir / "Hideout"
        if not self.hideout_dir.exists():  # tolerate lowercase folder name
            alt = self.data_dir / "hideout"
            if alt.exists():
                self.hideout_dir = alt
        self.hideout_benches: Dict[str, dict] = {}
        # item_id -> list of usage entries {bench_id, level, quantity}
        self.hideout_usage: Dict[str, List[dict]] = {}

        # Projects (expeditions) data
        self.projects_file = self.data_dir / "projects.json"
        self.projects: List[dict] = []
        # Set of all item IDs required for projects
        self.project_required_items: set = set()

    def load_all_items(self):
        """Load all item JSON files and hideout benches."""
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

        # Load hideout benches (non-fatal if missing)
        self._load_hideout_benches()
        self._build_hideout_usage()

        # Load projects (expeditions) data
        self._load_projects()

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

        For weapons/items that have tier variants (e.g., anvil_i, anvil_ii),
        if the base ID (e.g., anvil) is not found, automatically tries with "_i" suffix.

        Args:
            item_id: The item's unique identifier

        Returns:
            Item data dictionary or None if not found
        """
        # Try direct lookup first
        item = self.items.get(item_id)

        # If not found and doesn't end with tier suffix, try with "_i" suffix
        if item is None and not item_id.endswith(('_i', '_ii', '_iii', '_iv', '_v')):
            # Check if a tier I variant exists (for weapons/tiered items)
            tier_i_id = f"{item_id}_i"
            item = self.items.get(tier_i_id)
            if item:
                print(f"[INFO] Mapped base ID '{item_id}' -> '{tier_i_id}'")

        return item

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

    # ---------------- Hideout benches -----------------
    def _load_hideout_benches(self):
        """Load all hideout bench JSON files if directory exists."""
        if not self.hideout_dir.exists():
            return
        for json_file in self.hideout_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    bench_data = json.load(f)
                    bench_id = bench_data.get('id') or json_file.stem
                    self.hideout_benches[bench_id] = bench_data
            except json.JSONDecodeError as e:
                print(f"Error parsing hideout bench {json_file.name}: {e}")
            except Exception as e:
                print(f"Error loading hideout bench {json_file.name}: {e}")

    def _build_hideout_usage(self):
        """Build reverse mapping of item -> list of benches/levels where required."""
        self.hideout_usage = {}
        for bench_id, bench in self.hideout_benches.items():
            levels = bench.get('levels', [])
            for level_entry in levels:
                level_num = level_entry.get('level')
                reqs = level_entry.get('requirementItemIds', [])
                if not isinstance(reqs, list):
                    continue
                for req in reqs:
                    if not isinstance(req, dict):
                        continue
                    item_id = req.get('itemId')
                    quantity = req.get('quantity', 1)
                    if not item_id:
                        continue
                    self.hideout_usage.setdefault(item_id, []).append({
                        'bench_id': bench_id,
                        'level': level_num,
                        'quantity': quantity
                    })

    def get_hideout_usage(self, item_id: str) -> List[dict]:
        """Return list of hideout usage entries for given item id."""
        return self.hideout_usage.get(item_id, [])

    def get_hideout_bench(self, bench_id: str) -> Optional[dict]:
        """Return hideout bench data by id."""
        return self.hideout_benches.get(bench_id)

    def get_available_tiers(self, item_id: str) -> List[int]:
        """
        Get list of available tier numbers for an item.

        For items like 'anvil_i', checks if anvil_ii, anvil_iii, etc. exist.
        For base items like 'anvil', checks if anvil_i, anvil_ii, etc. exist.

        Args:
            item_id: Item ID (can be base or with tier suffix)

        Returns:
            List of tier numbers (1-5) that exist for this item, or empty list if no tiers
        """
        # Extract base item ID by removing tier suffix if present
        base_id = item_id
        for suffix in ('_v', '_iv', '_iii', '_ii', '_i'):
            if item_id.endswith(suffix):
                base_id = item_id[:-len(suffix)]
                break

        # Check which tier files exist
        available_tiers = []
        tier_suffixes = [('_i', 1), ('_ii', 2), ('_iii', 3), ('_iv', 4), ('_v', 5)]

        for suffix, tier_num in tier_suffixes:
            tier_id = f"{base_id}{suffix}"
            if tier_id in self.items:
                available_tiers.append(tier_num)

        return available_tiers

    # ---------------- Projects (Expeditions) -----------------
    def _load_projects(self):
        """Load projects.json and build set of required item IDs."""
        if not self.projects_file.exists():
            return

        try:
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                self.projects = json.load(f)

            # Build set of all required item IDs from all phases
            for project in self.projects:
                phases = project.get('phases', [])
                for phase in phases:
                    requirements = phase.get('requirementItemIds', [])
                    for req in requirements:
                        if isinstance(req, dict):
                            item_id = req.get('itemId')
                            if item_id:
                                self.project_required_items.add(item_id)

        except json.JSONDecodeError as e:
            print(f"Error parsing projects.json: {e}")
        except Exception as e:
            print(f"Error loading projects.json: {e}")

    def is_required_for_project(self, item_id: str) -> bool:
        """
        Check if an item is required for any project phase.

        Args:
            item_id: The item's unique identifier

        Returns:
            True if item is required for projects, False otherwise
        """
        return item_id in self.project_required_items
