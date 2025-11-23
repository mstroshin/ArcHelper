"""
Тестовый скрипт для проверки загрузки данных предметов.
Test script for verifying item data loading.
"""

import sys
from pathlib import Path
from src.data_loader import ItemDatabase

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_data_loader():
    """Тестирование загрузки базы данных предметов."""

    print("=" * 60)
    print("Тест загрузки базы данных предметов")
    print("Testing Item Database Loading")
    print("=" * 60)

    # Инициализация базы данных
    data_dir = Path(__file__).parent / "Data"
    db = ItemDatabase(data_dir)

    print("\n1. Загрузка всех предметов...")
    print("   Loading all items...")
    db.load_all_items()
    print(f"   ✓ Загружено предметов: {len(db.items)}")
    print(f"   ✓ Loaded items: {len(db.items)}")

    # Тест получения конкретного предмета
    print("\n2. Тест получения предмета 'adrenaline_shot'...")
    print("   Testing get item 'adrenaline_shot'...")
    item = db.get_item('adrenaline_shot')

    if item:
        print(f"   ✓ Название (EN): {item['name']['en']}")
        print(f"   ✓ Название (RU): {item['name']['ru']}")
        print(f"   ✓ Тип: {item['type']}")
        print(f"   ✓ Редкость: {item['rarity']}")

        if 'recipe' in item:
            print(f"   ✓ Рецепт крафта: {item['recipe']}")

        if 'recyclesInto' in item:
            print(f"   ✓ При разборке даёт: {item['recyclesInto']}")

        if 'salvagesInto' in item:
            print(f"   ✓ При утилизации даёт: {item['salvagesInto']}")
    else:
        print("   ✗ Предмет не найден!")

    # Тест обратного маппинга (что можно скрафтить из материала)
    print("\n3. Тест обратного маппинга для 'arc_alloy'...")
    print("   Testing reverse mapping for 'arc_alloy'...")
    items_using_alloy = db.get_items_using_material('arc_alloy')

    if items_using_alloy:
        print(f"   ✓ Найдено предметов, использующих 'arc_alloy': {len(items_using_alloy)}")
        print(f"   ✓ Found items using 'arc_alloy': {len(items_using_alloy)}")
        print("\n   Примеры (первые 5):")
        print("   Examples (first 5):")
        for item_data in items_using_alloy[:5]:
            recipe_amount = item_data.get('recipe', {}).get('arc_alloy', 0)
            print(f"     - {item_data['name']['en']} (требует {recipe_amount} ARC Alloy)")
    else:
        print("   ℹ Нет предметов, использующих этот материал")

    # Тест поиска по имени
    print("\n4. Тест поиска по имени 'grenade'...")
    print("   Testing search by name 'grenade'...")
    results = db.search_by_name('grenade', 'en')

    if results:
        print(f"   ✓ Найдено предметов: {len(results)}")
        print(f"   ✓ Found items: {len(results)}")
        for item_data in results[:5]:
            print(f"     - {item_data['name']['en']} ({item_data['id']})")
    else:
        print("   ℹ Ничего не найдено")

    # Статистика по типам предметов
    print("\n5. Статистика по типам предметов...")
    print("   Item type statistics...")
    types_count = {}
    for item_data in db.items.values():
        item_type = item_data.get('type', 'Unknown')
        types_count[item_type] = types_count.get(item_type, 0) + 1

    print("   Топ-10 типов предметов:")
    print("   Top 10 item types:")
    for item_type, count in sorted(types_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     - {item_type}: {count}")

    # Статистика по редкости
    print("\n6. Статистика по редкости...")
    print("   Rarity statistics...")
    rarity_count = {}
    for item_data in db.items.values():
        rarity = item_data.get('rarity', 'Unknown')
        rarity_count[rarity] = rarity_count.get(rarity, 0) + 1

    for rarity, count in sorted(rarity_count.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {rarity}: {count}")

    # Предметы с рецептами
    print("\n7. Предметы с рецептами крафта...")
    print("   Items with crafting recipes...")
    items_with_recipes = [item for item in db.items.values() if 'recipe' in item]
    print(f"   ✓ Предметов с рецептами: {len(items_with_recipes)}")

    # Материалы, используемые чаще всего
    print("\n8. Самые популярные материалы в рецептах...")
    print("   Most popular materials in recipes...")
    material_usage = {}
    for item_data in db.items.values():
        recipe = item_data.get('recipe', {})
        for material in recipe.keys():
            material_usage[material] = material_usage.get(material, 0) + 1

    if material_usage:
        print("   Топ-10 материалов:")
        print("   Top 10 materials:")
        for material, count in sorted(material_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
            material_name = db.get_item(material)
            if material_name:
                print(f"     - {material_name['name']['en']} ({material}): используется в {count} рецептах")
            else:
                print(f"     - {material}: используется в {count} рецептах")

    print("\n" + "=" * 60)
    print("✓ Все тесты завершены!")
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_data_loader()
