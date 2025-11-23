"""
Простой тест для быстрой проверки основной функциональности.
Simple test for quick functionality check.
"""

from pathlib import Path
from src.data_loader import ItemDatabase


def main():
    # Загрузка базы данных
    print("Загрузка базы данных предметов...")
    data_dir = Path(__file__).parent / "Data"
    db = ItemDatabase(data_dir)
    db.load_all_items()

    print(f"Загружено предметов: {len(db.items)}\n")

    # Интерактивный режим
    print("Введите ID предмета для просмотра информации (или 'quit' для выхода)")
    print("Примеры: adrenaline_shot, arc_alloy, bandage")
    print("-" * 60)

    while True:
        user_input = input("\nВведите ID предмета: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("До свидания!")
            break

        if not user_input:
            continue

        # Поиск предмета
        item = db.get_item(user_input)

        if not item:
            # Попробовать поиск по имени
            results = db.search_by_name(user_input, 'en')
            if results:
                print(f"\nНайдено {len(results)} совпадений по имени:")
                for idx, result in enumerate(results[:10], 1):
                    print(f"  {idx}. {result['name']['en']} (ID: {result['id']})")
                continue
            else:
                print(f"Предмет '{user_input}' не найден. Попробуйте другой ID.")
                continue

        # Вывод информации о предмете
        print("\n" + "=" * 60)
        print(f"Название: {item['name']['en']}")
        if 'ru' in item['name']:
            print(f"Название (RU): {item['name']['ru']}")
        print(f"ID: {item['id']}")
        print(f"Тип: {item.get('type', 'N/A')}")
        print(f"Редкость: {item.get('rarity', 'N/A')}")
        print(f"Вес: {item.get('weightKg', 'N/A')} кг")
        print(f"Размер стака: {item.get('stackSize', 'N/A')}")

        # Описание
        if 'description' in item:
            desc_en = item['description'].get('en', '')
            if desc_en:
                print(f"\nОписание: {desc_en}")

        # Рецепт крафта
        if 'recipe' in item:
            print(f"\nРецепт крафта:")
            for material_id, amount in item['recipe'].items():
                material = db.get_item(material_id)
                material_name = material['name']['en'] if material else material_id
                print(f"  - {material_name}: {amount}")

            if 'craftBench' in item:
                print(f"Верстак: {item['craftBench']}")

        # Разборка
        if 'recyclesInto' in item:
            print(f"\nПри разборке даёт:")
            for material_id, amount in item['recyclesInto'].items():
                material = db.get_item(material_id)
                material_name = material['name']['en'] if material else material_id
                print(f"  - {material_name}: {amount}")

        # Утилизация
        if 'salvagesInto' in item:
            print(f"\nПри утилизации даёт:")
            for material_id, amount in item['salvagesInto'].items():
                material = db.get_item(material_id)
                material_name = material['name']['en'] if material else material_id
                print(f"  - {material_name}: {amount}")

        # Что можно скрафтить из этого материала
        items_using = db.get_items_using_material(item['id'])
        if items_using:
            print(f"\nИспользуется для крафта ({len(items_using)} предметов):")
            for used_item in items_using[:5]:
                amount = used_item.get('recipe', {}).get(item['id'], 0)
                print(f"  - {used_item['name']['en']} (требует {amount})")
            if len(items_using) > 5:
                print(f"  ... и ещё {len(items_using) - 5} предметов")

        print("=" * 60)


if __name__ == "__main__":
    main()
