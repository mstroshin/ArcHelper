# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArcHelperPy is a game overlay assistant for Ark Raiders that helps players identify items and understand their crafting recipes and recycling components. The application is designed to run as a non-intrusive overlay on Windows:

- Players hover their mouse over an item in-game and press a hotkey
- The program captures the item icon (fixed size, e.g., 200x200px)
- Image recognition identifies the item
- An overlay displays useful information about the item's crafting recipes, recycling outputs, and salvage components

**Critical constraint**: The application must not interfere with the game or trigger anti-cheat systems. It should be a passive overlay tool only.

## Technology Stack

- **Language**: Python 3.13
- **Target Platform**: Windows

## Data Architecture

### Item Data Structure

The project contains 448 game items stored in `Data/Items/` with two components per item:
- **JSON file**: Contains complete item metadata (`Data/Items/<item_id>.json`)
- **PNG icon**: Item image for recognition (`Data/Items/Images/<item_id>.png`)

### JSON Schema

Each item JSON follows this structure:

```json
{
  "id": "unique_item_id",
  "name": { "en": "English Name", ... },  // Multilingual support (22 languages)
  "description": { "en": "Description", ... },
  "type": "Item Type",  // e.g., "Quick Use", "Topside Material"
  "rarity": "Common|Uncommon|Rare|...",
  "value": 300,  // In-game value
  "weightKg": 0.2,
  "stackSize": 5,

  // Crafting and recycling relationships
  "recipe": { "material1": count, "material2": count },  // Optional: ingredients needed to craft this item
  "craftBench": "bench_id",  // Optional: required crafting station
  "recyclesInto": { "material1": count, "material2": count },  // Optional: items obtained when recycled
  "salvagesInto": { "material1": count },  // Optional: items obtained when salvaged

  // Additional metadata
  "effects": { ... },  // Optional: item effects with values
  "imageFilename": "https://cdn.arctracker.io/items/<item_id>.png",
  "updatedAt": "MM/DD/YYYY"
}
```

**Key relationships**:
- `recipe`: Shows what materials are needed to craft this item
- `craftBench`: The crafting station required (e.g., "med_station", "workbench")
- `recyclesInto`: Materials obtained when recycling the item (disassembling)
- `salvagesInto`: Materials obtained when salvaging the item (alternative breakdown method)

## Core Requirements

### Image Recognition System
- Item icons are fixed-size images (specified as 200x200px in PRD)
- Local PNG files in `Data/Items/Images/` should be used as reference templates
- Image recognition must match captured screen regions against the 448 item templates
- Consider using OpenCV, Pillow, or similar libraries for image matching

### Overlay Display
- Must display over the game window without injecting into the game process
- Should show:
  - Item name and description
  - What materials it recycles into (`recyclesInto`)
  - What materials it salvages into (`salvagesInto`)
  - What it can be crafted into (requires reverse lookup - find items that have this item in their `recipe`)
  - Crafting recipe if applicable (`recipe`, `craftBench`)
  - Item stats (rarity, value, weight, effects)

### Hotkey System
- Global hotkey detection while game is in focus
- Must not interfere with game input

## Development Notes

### Data Loading
When loading item data:
- Parse all 448 JSON files from `Data/Items/*.json`
- Build a reverse mapping for "what uses this material" by scanning all `recipe` fields
- Index items by their `id` for quick lookup after image recognition

### Language Support
All items include translations in 22 languages. Consider making the overlay language-configurable:
`en, de, fr, es, pt, pl, no, da, it, ru, ja, zh-TW, uk, zh-CN, kr, tr, hr, sr`

### Anti-Cheat Safety
- Do NOT hook into game process memory
- Do NOT inject any DLLs into the game
- Only use screen capture and overlay rendering
- Operate as a separate process
