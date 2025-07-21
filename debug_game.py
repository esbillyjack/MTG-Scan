#!/usr/bin/env python3

import sys
import traceback

print("Starting Aces Pup game debug...")

try:
    print("Importing pygame...")
    import pygame
    print(f"Pygame version: {pygame.version.ver}")
    
    print("Initializing pygame...")
    pygame.init()
    print("Pygame initialized successfully")
    
    print("Setting up display...")
    screen = pygame.display.set_mode((1200, 800))
    print("Display set up successfully")
    
    print("Loading game assets...")
    # Test loading assets
    try:
        logo = pygame.image.load("art_dump/aces_logo.png")
        print("Logo loaded successfully")
    except Exception as e:
        print(f"Error loading logo: {e}")
    
    try:
        pygame.mixer.music.load("art_dump/groove.wav")
        print("Music loaded successfully")
    except Exception as e:
        print(f"Error loading music: {e}")
    
    print("Creating game instance...")
    import main
    game_instance = main.game()
    print("Game instance created successfully")
    
    print("Starting game loop...")
    game_instance.run()
    
except Exception as e:
    print(f"Error occurred: {e}")
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1) 