"""Debug script to find Simple Gun Parts ranking."""

from src.data_loader import ItemDatabase
from src.image_recognition import ItemRecognizer
from pathlib import Path
import cv2

# Load database and recognizer
db = ItemDatabase(Path('Data'))
db.load_all_items()
rec = ItemRecognizer(Path('Data'), db)
rec.load_templates()

# Load test image
test_img = cv2.imread('TestImages/simple_gun_parts.png')

# Get all matches
all_matches = rec.get_top_matches(test_img, 300)

# Find Simple Gun Parts
for i, (item_id, score) in enumerate(all_matches, 1):
    item = db.get_item(item_id)
    if item and 'simple gun' in item['name']['en'].lower():
        print(f'Rank {i}: {item["name"]["en"]}: {score:.2%}')
        break
else:
    print("Simple Gun Parts not found in top 300 matches!")

# Also show what simple_gun_parts actually looks like as a template
if 'simple_gun_parts' in rec.templates:
    template, _ = rec.templates['simple_gun_parts']
    print(f'\nTemplate shape: {template.shape}')
    print(f'Test image shape: {test_img.shape}')
