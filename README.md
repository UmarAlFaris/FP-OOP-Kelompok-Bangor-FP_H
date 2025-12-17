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
├── assets/              # All game assets
│   ├── boss/           # Boss character sprites
│   ├── enderman/       # Enderman character sprites
│   ├── player/         # Player character sprites
│   ├── skeleton/       # Skeleton character sprites
│   ├── zombie/         # Zombie character sprites
│   └── ui/             # UI images and backgrounds
├── src/                 # Source code
│   ├── main.py         # Main game logic
│   ├── screen_manager.py  # Screen/scene management
│   ├── ai/             # AI and fuzzy logic modules
│   │   └── fuzzy_logic.py
│   ├── scenes/         # Game scenes
│   │   ├── base.py
│   │   ├── fight_base.py
│   │   ├── main_menu.py
│   │   ├── video_scene_base.py
│   │   └── S*.py       # Scene files
│   └── ui/             # UI components
│       └── button.py
└── legacy/             # Legacy prototype code (archived)
    └── Code/
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

