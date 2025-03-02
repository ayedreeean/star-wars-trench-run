import pygame
import math
from pygame.locals import *
import random
import asyncio
import platform
import sys

# Initialize Pygame
pygame.init()

# Set up the display
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Don't create the screen here - move it into main()
# screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

# Keep all your original constants and class definitions here...

async def main():
    try:
        # Initialize display with proper flags for web
        if platform.system() == "Emscripten":
            canvas = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
                                          flags=pygame.RESIZABLE)
        else:
            canvas = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            
        pygame.display.set_caption("Star Wars Trench Run")
        
        # Get the screen surface
        screen = pygame.display.get_surface()
        
        # Keep all your original game initialization code...
        player = Player()
        tie_fighters = []
        health_powerups = []
        powerup_timer = 0
        lasers = []
        enemy_lasers = []
        spawn_timer = 0
        
        # Create temp_surface once
        temp_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Game loop
        running = True
        clock = pygame.time.Clock()

        while running:
            # Add web compatibility pause
            if platform.system() == "Emscripten":
                await asyncio.sleep(0)
            
            # Keep all your original game loop code...
            
            # Make sure to update the display at the end
            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        pygame.quit()

# Entry point
if __name__ == "__main__":
    asyncio.run(main()) 