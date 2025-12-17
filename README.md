# FP-OOP-Kelompok-Bangor-FP_H
FP OOP Kelompok Bangor FP_H

JANGAN LUPA SEBELUM NGEDIT DI FETCH ORIGIN DI GITHUB DESKTOP BARU DI PULL BARU DI EDIT FILENYA

Nama Kontirbutor:
- Umar Al Faris - 5054241015
- Muhammad Hadidan Nurhaunan - 5054241016

# VIVA Fantasy: Calvin Origin

Projek ini dibuat berdasarkan Minecraft Roleplay yang dibuat oleh tim VIFAN dan Youtuber ElestialHD.
Seluruh cerita yang berada pada game ini sudah di ubah sedikit demi menyesuaikan kebutuhan dalam game.
Game ini berjalan dengan basis Turn Based-RPG yang mengambil POV dari Villain utama Season 2 yaitu Calvin, sang King of Diamond.

## Project Structure

The project has been refactored to follow professional Python standards and PEP 8 conventions:

```
FP-OOP-Kelompok-Bangor-FP_H/
├── run_game.py          # Main entry point to run the game
├── highscore.json       # High score data
├── README.md            # Project documentation
├── assets/              # All game assets
│   ├── battlefield/    # Battlefield backgrounds
│   ├── boss/           # Boss character sprites
│   ├── enderman/       # Enderman character sprites
│   ├── player/         # Player character sprites
│   ├── skeleton/       # Skeleton character sprites
│   ├── zombie/         # Zombie character sprites
│   ├── sounds/         # Game sound effects and music
│   └── ui/             # UI images and backgrounds
└── src/                # Source code
    ├── main.py         # Main game logic
    ├── screen_manager.py  # Screen/scene management
    ├── config.py       # Game configuration
    ├── utils.py        # Utility functions
    ├── ai/             # AI and fuzzy logic modules
    │   └── fuzzy_logic.py
    ├── entities/       # Game entities (characters, enemies)
    │   ├── __init__.py
    │   ├── base.py     # Base entity class
    │   ├── player.py   # Player entity
    │   ├── enemies.py  # Enemy entities
    │   └── boss.py     # Boss entity
    ├── scenes/         # Game scenes
    │   ├── __init__.py
    │   ├── base.py     # Base scene class
    │   ├── fight_base.py  # Base fight scene
    │   ├── main_menu.py   # Main menu scene
    │   ├── battle_scene.py  # Battle scene
    │   ├── crossroads.py    # Crossroads scene
    │   ├── end_menu.py      # End menu scene
    │   ├── high_score.py    # High score scene
    │   └── components/      # Scene components
    │       ├── __init__.py
    │       ├── battle_assets.py   # Battle assets manager
    │       ├── battle_renderer.py # Battle rendering
    │       └── battle_ui.py       # Battle UI components
    └── ui/             # UI components
        ├── __init__.py
        └── button.py   # Button component
```

## How to Run

Run the game using the entry point script:

```bash
python run_game.py
```

## Requirements

- Python 3.x
- pygame
- cv2 (opencv-python)
- numpy
- scikit-fuzzy (for AI logic)

