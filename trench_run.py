import pygame
import math
from pygame.locals import *
import random
import asyncio
import platform
import sys

# Initialize Pygame with proper flags for web
pygame.init()

# Set up the display with proper flags for web
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Remove the early screen initialization
# screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
# pygame.display.set_caption("Star Wars Trench Run")

# Rest of your constants...

async def main():
    try:
        # Initialize display with proper flags for web
        if platform.system() == "Emscripten":
            pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
                                  flags=pygame.OPENGL | 
                                        pygame.DOUBLEBUF | 
                                        pygame.RESIZABLE)
        else:
            pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            
        pygame.display.set_caption("Star Wars Trench Run")
        
        # Create the screen surface after initialization
        screen = pygame.display.get_surface()
        
        # Rest of your game initialization...
        
        while running:
            try:
                # Add proper web frame timing
                if platform.system() == "Emscripten":
                    await asyncio.sleep(0)  # Required for web
                
                # Rest of your game loop...
                
                # Make sure to flip the display at the end of each frame
                pygame.display.flip()
                
                # Control frame rate
                clock.tick(60)
                
            except Exception as e:
                print(f"Error in game loop: {e}")
                break
                
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        pygame.quit()

# Web-specific entry point
if __name__ == "__main__":
    asyncio.run(main()) 