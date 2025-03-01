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
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Star Wars Trench Run")

# Colors
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
MEDIUM_GRAY = (80, 80, 80)  # New color for grid lines

# Player (X-wing) properties
player_x = WINDOW_WIDTH // 2
player_y = WINDOW_HEIGHT // 2
player_speed = 7

# Laser properties
lasers = []
LASER_SPEED = 9.4

# Trench properties
TRENCH_SEGMENTS = 20
segment_width = WINDOW_WIDTH
segment_spacing = 50

# Add to the top with other properties
SCROLL_SPEED = 3.75
trench_offset = 0

# Add to the top with other properties
HEALTH_MAX = 100
HEALTH_WIDTH = WINDOW_WIDTH  # Make health bar full screen width
HEALTH_HEIGHT = 8  # Increased from 3 to 8 pixels
HEALTH_DAMAGE = 10  # Changed from 5 to 10 (10% damage per hit)

# Add to player properties
player_health = HEALTH_MAX

# Add to the top with other properties
SHAKE_AMOUNT = 30
SHAKE_DURATION = 30

# Add to the top with other constants
COLLISION_DAMAGE = 15  # 15% damage for TIE fighter collisions
SCORE_PER_TIE = 10

# Add to the top with other constants
TURRET_INTERVAL = 12  # Changed from 6 to 12 (much fewer turrets)
TURRET_SHOOT_INTERVAL = 120  # Frames between shots

# Add new constants for the exhaust port challenge
EXHAUST_PORT_SIZE = 20
# PERFECT_TIMING_WINDOW = 1.2  # Increased from 0.8 to 1.2 seconds
# GOOD_TIMING_WINDOW = 2.0    # Increased from 1.5 to 2.0 seconds

# Add new constants for end game states
GAME_STATE_PLAYING = 0
GAME_STATE_VICTORY = 1
GAME_STATE_FAILURE = 2

# Add new constants for difficulty scaling
BASE_SCROLL_SPEED = 3.75  # Keep initial speed
MAX_SCROLL_SPEED = 12.0   # Keep max speed
SPEED_INCREASE_RATE = 0.02  # Doubled from 0.01 to 0.02 (much faster acceleration)
BASE_SPAWN_INTERVAL = 80  # Original spawn interval
MIN_SPAWN_INTERVAL = 30  # Decreased from 40 to 30 (even faster spawning at max difficulty)

# Add new constants for health power-ups
HEALTH_POWERUP_INTERVAL = 900  # Keep at 15 seconds
HEALTH_RESTORE_AMOUNT = 30  # Reduced from 50 to 30 points
POWERUP_SPEED = 2.5  # Keep same speed

# Update health powerup constants
PINK = (255, 192, 203)  # Add pink color for hearts

class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = 0  # Distance into the trench

    def move(self):
        self.z += LASER_SPEED

    def draw(self, temp_surface):
        # Calculate perspective scaling
        scale = 1 / (self.z * 0.01 + 1)
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Make laser trail longer
        next_scale = 1 / ((self.z + 60) * 0.01 + 1)
        end_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * next_scale
        end_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * next_scale
        
        # Thicker laser beam
        laser_width = max(3, 7 * scale)
        pygame.draw.line(temp_surface, GREEN, (screen_x, screen_y), (end_x, end_y), int(laser_width))

class Explosion:
    def __init__(self, x, y, z, size=20):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.lifetime = 8
        self.current_frame = 0

    def update(self):
        self.current_frame += 1
        return self.current_frame < self.lifetime
        
    def draw(self, temp_surface):
        if self.current_frame >= self.lifetime:
            return
            
        scale = 1 / (self.z * 0.01 + 1)
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Calculate sizes and alphas for both circles
        progress = self.current_frame / self.lifetime
        size = self.size * scale * (1 - progress * 0.3)
        
        # White inner circle
        white_alpha = int(255 * (1 - progress))
        white_size = size * 0.6  # Inner circle is smaller
        pygame.draw.circle(temp_surface, (*WHITE, white_alpha), 
                         (int(screen_x), int(screen_y)), 
                         int(white_size))
        
        # Yellow outer circle
        yellow_alpha = int(200 * (1 - progress))  # Slightly more transparent
        pygame.draw.circle(temp_surface, (*YELLOW, yellow_alpha), 
                         (int(screen_x), int(screen_y)), 
                         int(size))

class TieFighter:
    def __init__(self, x, z):
        self.x = x
        self.y = WINDOW_HEIGHT/2 + random.randint(-int(WINDOW_HEIGHT/4), int(WINDOW_HEIGHT/4))
        self.z = z
        self.speed = (SCROLL_SPEED + 1) * 1.1  # Updated to use new scroll speed
        self.hit = False
        self.shoot_timer = random.randint(30, 90)

    def move(self):
        self.z -= self.speed
        self.shoot_timer -= 1
        
    def should_shoot(self):
        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(60, 120)
            return True
        return False
        
    def is_visible(self):
        # Calculate screen position with perspective
        scale = 1 / (self.z * 0.01 + 1)
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Increase the buffer zone for visibility check
        buffer = 100  # Increased from 50
        return (screen_x > -buffer and screen_x < WINDOW_WIDTH + buffer and
                screen_y > -buffer and screen_y < WINDOW_HEIGHT + buffer)
        
    def draw(self, temp_surface):
        # Calculate perspective scaling
        scale = 1 / (self.z * 0.01 + 1)
        
        # Calculate screen position with perspective
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Size of TIE fighter elements with perspective
        body_radius = int(9 * scale)
        wing_size = int(22 * scale)
        
        # Calculate alpha based on z position (fade out as it passes player)
        alpha = 255
        if self.z < 0:  # Start fading only after passing player (z < 0)
            # Fade over a longer distance (-200 to 0)
            fade_distance = 200
            alpha = max(0, int(255 * (1 + self.z / fade_distance)))
        
        # Create a surface for the TIE fighter with transparency
        surface_size = wing_size * 4
        tie_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        
        # Center position on surface
        center_x = surface_size // 2
        center_y = surface_size // 2
        
        # Draw the spherical cockpit
        pygame.draw.circle(tie_surface, (*WHITE, alpha), (center_x, center_y), body_radius)
        
        # Draw the wings
        wing_color = (*WHITE, alpha)  # White with transparency
        
        # Left wing
        pygame.draw.polygon(tie_surface, wing_color, [
            (center_x - wing_size, center_y),
            (center_x - wing_size//2, center_y - wing_size//2),
            (center_x - wing_size//2, center_y + wing_size//2)
        ])
        
        # Right wing
        pygame.draw.polygon(tie_surface, wing_color, [
            (center_x + wing_size, center_y),
            (center_x + wing_size//2, center_y - wing_size//2),
            (center_x + wing_size//2, center_y + wing_size//2)
        ])
        
        # Draw the surface to the temp_surface instead of screen
        temp_surface.blit(tie_surface, 
                       (int(screen_x - surface_size//2), 
                        int(screen_y - surface_size//2)))

class EnemyLaser:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.speed = LASER_SPEED * 0.7  # Slightly slower than player lasers

    def move(self):
        self.z -= (self.speed + SCROLL_SPEED)  # Move toward player

    def is_visible(self):
        # Calculate screen position with perspective
        scale = 1 / (self.z * 0.01 + 1)
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Check if laser is still on screen with some buffer
        buffer = 100
        return (screen_x > -buffer and screen_x < WINDOW_WIDTH + buffer and
                screen_y > -buffer and screen_y < WINDOW_HEIGHT + buffer)

    def draw(self, temp_surface):
        scale = 1 / (self.z * 0.01 + 1)
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Make laser trail longer
        next_scale = 1 / ((self.z + 60) * 0.01 + 1)
        end_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * next_scale
        end_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * next_scale
        
        # Thicker laser beam
        laser_width = max(3, 6 * scale)
        pygame.draw.line(temp_surface, RED, (screen_x, screen_y), (end_x, end_y), int(laser_width))

def draw_trench(temp_surface):
    global trench_offset
    
    # Update the offset
    trench_offset = (trench_offset + SCROLL_SPEED) % segment_spacing
    
    for i in range(TRENCH_SEGMENTS):
        # Calculate perspective scaling
        depth = (i * segment_spacing) - trench_offset  # Subtract offset here
        scale = 1 / (depth * 0.01 + 1)
        
        # Skip segments that would be behind the camera
        if depth < 0:
            continue
            
        # Calculate width at this depth
        left_x = WINDOW_WIDTH/2 + (-WINDOW_WIDTH/2.5) * scale
        right_x = WINDOW_WIDTH/2 + (WINDOW_WIDTH/2.5) * scale
        
        # Calculate heights for perspective
        top_y = WINDOW_HEIGHT/2 + (-WINDOW_HEIGHT/2) * scale
        bottom_y = WINDOW_HEIGHT/2 + (WINDOW_HEIGHT/2) * scale
        
        # Draw trench walls
        wall_width = 2
        # Left wall
        pygame.draw.line(temp_surface, MEDIUM_GRAY, 
                        (left_x, top_y),
                        (left_x, bottom_y),
                        2)
        # Right wall
        pygame.draw.line(temp_surface, MEDIUM_GRAY,
                        (right_x, top_y),
                        (right_x, bottom_y),
                        2)
        # Floor line only
        pygame.draw.line(temp_surface, MEDIUM_GRAY, 
                        (left_x, bottom_y),
                        (right_x, bottom_y))

def draw_player(temp_surface, player):
    # Center circle (engine)
    pygame.draw.circle(temp_surface, WHITE, (player.x, player.y), 10)
    
    # Four engine circles - adjusted positions to be more horizontal
    engine_radius = 5
    pygame.draw.circle(temp_surface, WHITE, (player.x - 16, player.y - 8), engine_radius)  # Top left
    pygame.draw.circle(temp_surface, WHITE, (player.x + 16, player.y - 8), engine_radius)  # Top right
    pygame.draw.circle(temp_surface, WHITE, (player.x - 16, player.y + 8), engine_radius)  # Bottom left
    pygame.draw.circle(temp_surface, WHITE, (player.x + 16, player.y + 8), engine_radius)  # Bottom right
    
    # Engine glow
    glow_color = (255, 165, 0)
    glow_radius = 2
    pygame.draw.circle(temp_surface, glow_color, (player.x - 16, player.y - 8), glow_radius)
    pygame.draw.circle(temp_surface, glow_color, (player.x + 16, player.y - 8), glow_radius)
    pygame.draw.circle(temp_surface, glow_color, (player.x - 16, player.y + 8), glow_radius)
    pygame.draw.circle(temp_surface, glow_color, (player.x + 16, player.y + 8), glow_radius)
    
    # X-shaped wings
    wing_length = 35
    wing_width = 3
    
    # Draw the four wings
    pygame.draw.line(temp_surface, WHITE, 
                    (player.x - 16, player.y - 8),
                    (player.x - wing_length, player.y - 15),
                    wing_width)
    pygame.draw.line(temp_surface, WHITE,
                    (player.x + 16, player.y - 8),
                    (player.x + wing_length, player.y - 15),
                    wing_width)
    pygame.draw.line(temp_surface, WHITE,
                    (player.x - 16, player.y + 8),
                    (player.x - wing_length, player.y + 15),
                    wing_width)
    pygame.draw.line(temp_surface, WHITE,
                    (player.x + 16, player.y + 8),
                    (player.x + wing_length, player.y + 15),
                    wing_width)

# Remove the global player_health variable and add Player class
class Player:
    def __init__(self):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2
        self.speed = 7
        self.health = HEALTH_MAX
        self.shake_frames = 0  # Track screen shake duration
        self.hit_flash = False  # Track if player was just hit
        self.score = 0  # Add score tracking
        self.exhaust_port_hit = False
        self.final_shot_time = None
        self.game_state = GAME_STATE_PLAYING
        self.end_timer = 0  # For controlling end game sequences
        self.ties_destroyed = 0
        self.ties_total = 0  # Total TIE fighters that appeared
        self.time_survived = 0  # Track time for difficulty scaling

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.shake_frames = SHAKE_DURATION
        self.hit_flash = True
        # Create explosions
        for _ in range(4):
            offset_x = random.randint(-30, 30)
            offset_y = random.randint(-30, 30)
            size = random.randint(20, 40)
            explosions.append(Explosion(self.x + offset_x, self.y + offset_y, 0, size=size))
        
        # Check if player died
        if self.health <= 0:
            self.game_state = GAME_STATE_FAILURE
            create_victory_explosion()  # Big explosion for player death

    def update_shake(self):
        if self.shake_frames > 0:
            self.shake_frames -= 1
            if self.shake_frames <= 0:  # Ensure it resets completely
                self.shake_frames = 0
        self.hit_flash = False

    def get_shake_offset(self):
        if self.shake_frames > 0:
            dx = random.randint(-SHAKE_AMOUNT, SHAKE_AMOUNT)
            dy = random.randint(-SHAKE_AMOUNT, SHAKE_AMOUNT)
            shake_intensity = self.shake_frames / SHAKE_DURATION
            return dx * shake_intensity, dy * shake_intensity
        return 0, 0

    def draw_health_bar(self, temp_surface):
        if self.health > 0:
            health_rect = pygame.Rect(
                0,
                0,
                WINDOW_WIDTH * (self.health / HEALTH_MAX),
                HEALTH_HEIGHT
            )
            pygame.draw.rect(temp_surface, GREEN, health_rect)

    def add_score(self, points):
        self.score += points
    
    def draw_score(self, temp_surface):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.score}', True, WHITE)
        score_rect = score_text.get_rect()
        score_rect.topright = (WINDOW_WIDTH - 10, 10)
        temp_surface.blit(score_text, score_rect)

    def check_exhaust_port_shot(self):
        # Check if shot was fired in the timing window
        time_left = self.timer
        if 0 <= time_left <= PERFECT_TIMING_WINDOW:
            return "PERFECT!"
        elif 0 <= time_left <= GOOD_TIMING_WINDOW:
            return "GOOD!"
        return None

    def draw_end_game_message(self, temp_surface):
        font_large = pygame.font.Font(None, 74)
        font_med = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # Game Over message
        text = "GAME OVER"
        color = RED
        text_surface = font_large.render(text, True, color)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3))
        temp_surface.blit(text_surface, text_rect)
        
        # Stats display
        y_pos = WINDOW_HEIGHT/2 - 40
        spacing = 40
        
        # Final Score
        score_text = f"Final Score: {self.score}"
        score_surface = font_med.render(score_text, True, WHITE)
        score_rect = score_surface.get_rect(center=(WINDOW_WIDTH/2, y_pos))
        temp_surface.blit(score_surface, score_rect)
        
        # TIEs Destroyed
        ties_text = f"TIEs Destroyed: {self.ties_destroyed}"
        ties_surface = font_med.render(ties_text, True, WHITE)
        ties_rect = ties_surface.get_rect(center=(WINDOW_WIDTH/2, y_pos + spacing))
        temp_surface.blit(ties_surface, ties_rect)
        
        # Accuracy
        if self.ties_total > 0:
            accuracy = (self.ties_destroyed / self.ties_total) * 100
            accuracy_text = f"Accuracy: {accuracy:.1f}%"
            accuracy_surface = font_med.render(accuracy_text, True, WHITE)
            accuracy_rect = accuracy_surface.get_rect(center=(WINDOW_WIDTH/2, y_pos + spacing * 2))
            temp_surface.blit(accuracy_surface, accuracy_rect)
        
        # Time Survived
        time_text = f"Time Survived: {self.time_survived:.1f}s"
        time_surface = font_med.render(time_text, True, WHITE)
        time_rect = time_surface.get_rect(center=(WINDOW_WIDTH/2, y_pos + spacing * 3))
        temp_surface.blit(time_surface, time_rect)
        
        # Retry message
        if self.end_timer > 60:  # Wait a bit before showing retry message
            retry_text = font_small.render("Press SPACE to try again", True, WHITE)
            retry_rect = retry_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT * 3/4))
            temp_surface.blit(retry_text, retry_rect)

    def draw_stats(self, temp_surface):
        font = pygame.font.Font(None, 36)
        destroyed_text = f'TIEs Destroyed: {self.ties_destroyed}'
        destroyed_surface = font.render(destroyed_text, True, WHITE)
        temp_surface.blit(destroyed_surface, (10, 10))

    def draw_speed_indicator(self, temp_surface):
        font = pygame.font.Font(None, 36)
        speed_text = f'Speed: {SCROLL_SPEED:.1f} / {MAX_SCROLL_SPEED:.1f}'
        speed_surface = font.render(speed_text, True, WHITE)
        temp_surface.blit(speed_surface, (10, 50))

    def update_difficulty(self):
        # Increase time survived
        self.time_survived += 1/60
        
        # Calculate new scroll speed (twice as fast increase)
        global SCROLL_SPEED
        SCROLL_SPEED = min(MAX_SCROLL_SPEED, 
                          BASE_SCROLL_SPEED + (self.time_survived * SPEED_INCREASE_RATE))
        
        # Calculate new spawn interval (faster reduction to match speed)
        global SPAWN_INTERVAL
        spawn_reduction = self.time_survived * 1.0  # Doubled from 0.5 to 1.0
        SPAWN_INTERVAL = max(MIN_SPAWN_INTERVAL, 
                           BASE_SPAWN_INTERVAL - spawn_reduction)

# Create player instance before the game loop
player = Player()

# Add to the top with other properties
tie_fighters = []
TIE_SPAWN_DISTANCE = segment_spacing * (TRENCH_SEGMENTS - 2)  # Spawn near end of trench
SPAWN_INTERVAL = 80  # Reduced from 120 to 80 (50% faster spawning)
spawn_timer = 0

# Add to the top with other properties
explosions = []

# Add to the top with other properties
enemy_lasers = []

# Add this function before the game loop
def draw_targeting_computer(temp_surface, player):
    pass  # Disabled targeting computer
    """
    # Original targeting computer code commented out
    if player.timer > TARGETING_START_TIME:
        return
        
    time_progress = player.timer / TARGETING_START_TIME
    ...
    """

# Update chain explosion function to be much more efficient
def create_chain_explosion(x, y, z):
    # Single massive central explosion
    explosions.append(Explosion(x, y, z, size=500))  # One very large explosion
    
    # Just 4 large surrounding explosions
    for i in range(4):
        angle = (i / 4) * 2 * math.pi
        ring_x = x + math.cos(angle) * 300
        ring_y = y + math.sin(angle) * 300
        explosions.append(Explosion(ring_x, ring_y, z, size=300))
    
    # No delays, no multiple waves, just one more final explosion
    explosions.append(Explosion(x, y, z - 100, size=400))

# Update the TIE fighter collision section with better explosions
def create_tie_explosion(x, y, z):
    # Create a cluster of larger explosions
    for _ in range(4):  # Increased from 3 to 4 explosions
        offset_x = random.randint(-30, 30)  # Increased spread
        offset_y = random.randint(-30, 30)
        size = random.randint(40, 70)  # Increased from (30, 50)
        explosions.append(Explosion(x + offset_x, y + offset_y, z, size=size))

# Add new function for victory explosion
def create_victory_explosion():
    center_x = WINDOW_WIDTH/2
    center_y = WINDOW_HEIGHT/2
    z_pos = TRENCH_SEGMENTS * segment_spacing
    
    # Initial massive explosion
    explosions.append(Explosion(center_x, center_y, z_pos, size=1000))  # Increased from 800
    
    # Create expanding ring explosions
    for ring in range(4):  # Increased from 3 to 4 rings
        radius = 250 * (ring + 1)  # Increased from 200
        num_explosions = 10 + ring * 4  # Increased from 8
        for i in range(num_explosions):
            angle = (i / num_explosions) * 2 * math.pi
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            size = random.randint(300, 500)  # Increased from (200, 400)
            explosions.append(Explosion(x, y, z_pos, size=size))
    
    # Add more random explosions
    for _ in range(20):  # Increased from 15
        x = center_x + random.randint(-800, 800)  # Increased spread
        y = center_x + random.randint(-800, 800)
        z = z_pos + random.randint(-300, 300)
        size = random.randint(300, 600)  # Increased sizes
        explosions.append(Explosion(x, y, z, size=size))

# Add new constants for health power-ups
HEALTH_POWERUP_INTERVAL = 900  # Spawn every 15 seconds (at 60 FPS)
HEALTH_RESTORE_AMOUNT = 30  # Restore 30% health
POWERUP_SPEED = 2  # How fast powerups move toward player

class HealthPowerup:
    def __init__(self, x, z):
        self.x = x
        self.y = WINDOW_HEIGHT/2 + random.randint(-100, 100)
        self.z = z
        self.collected = False
        self.rotation = 0
        
    def move(self):
        self.z -= SCROLL_SPEED + POWERUP_SPEED
        self.rotation += 2  # Rotate the powerup
        
    def draw(self, temp_surface):
        scale = 1 / (self.z * 0.01 + 1)
        screen_x = WINDOW_WIDTH/2 + (self.x - WINDOW_WIDTH/2) * scale
        screen_y = WINDOW_HEIGHT/2 + (self.y - WINDOW_HEIGHT/2) * scale
        
        # Draw heart shape
        size = 25 * scale  # Increased from 15 to 25
        
        # Calculate heart points
        def heart_points(x, y, size):
            points = []
            for t in range(30):  # More points for smoother heart
                t = t * 2 * math.pi / 30
                # Heart shape formula
                x_offset = size * 16 * math.sin(t) ** 3
                y_offset = size * -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
                points.append((x + x_offset/16, y + y_offset/16))  # Scaled down to look better
            return points
        
        # Draw filled heart
        points = heart_points(screen_x, screen_y, size)
        if len(points) > 2:  # Need at least 3 points to draw polygon
            pygame.draw.polygon(temp_surface, PINK, points)
            # Draw outline slightly larger
            pygame.draw.polygon(temp_surface, (*PINK, 128), points, 2)  # Semi-transparent outline

# Add to game initialization
health_powerups = []
powerup_timer = 0

# Move the game loop into an async main function
async def main():
    try:
        # Initialize Pygame
        pygame.init()
        
        # For web compatibility, we need to wait for the context to be ready
        if platform.system() == "Emscripten":
            import platform
            import asyncio
            canvas = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
        else:
            canvas = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            
        pygame.display.set_caption("Star Wars Trench Run")
        
        # Declare global variables that will be modified
        global SCROLL_SPEED, SPAWN_INTERVAL, explosions  # Add explosions to global
        SCROLL_SPEED = BASE_SCROLL_SPEED
        explosions = []  # Initialize explosions list here
        
        # Create game objects
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
            try:
                # Add web compatibility pause
                if platform.system() == "Emscripten":
                    await asyncio.sleep(0)
                
                # Event handling
                for event in pygame.event.get():
                    if event.type == QUIT:
                        running = False
                    elif event.type == KEYDOWN:
                        if event.key == K_SPACE:
                            lasers.append(Laser(player.x, player.y - 10))

                # Update player movement
                keys = pygame.key.get_pressed()
                if keys[K_LEFT] and player.x > WINDOW_WIDTH/2 - WINDOW_WIDTH/2.0:
                    player.x -= player.speed
                if keys[K_RIGHT] and player.x < WINDOW_WIDTH/2 + WINDOW_WIDTH/2.0:
                    player.x += player.speed
                if keys[K_UP] and player.y > WINDOW_HEIGHT/8:
                    player.y -= player.speed
                if keys[K_DOWN] and player.y < WINDOW_HEIGHT - WINDOW_HEIGHT/12:
                    player.y += player.speed

                # Update lasers
                for laser in lasers[:]:
                    laser.move()
                    if laser.z > TRENCH_SEGMENTS * segment_spacing:
                        lasers.remove(laser)

                # Update and draw TIE fighters - only spawn if game is still playing
                if player.game_state == GAME_STATE_PLAYING:
                    spawn_timer += 1
                    if spawn_timer >= SPAWN_INTERVAL:
                        # Spawn new TIE fighter at random x position
                        spawn_x = WINDOW_WIDTH/2 + random.randint(-int(WINDOW_WIDTH/6), int(WINDOW_WIDTH/6))
                        tie_fighters.append(TieFighter(spawn_x, TIE_SPAWN_DISTANCE))
                        player.ties_total += 1  # Increment total TIEs
                        spawn_timer = 0
                
                # Check for collisions between lasers and TIE fighters
                for laser in lasers[:]:
                    for tie in tie_fighters[:]:
                        if not tie.hit:
                            # Calculate positions with perspective for both objects
                            laser_scale = 1 / (laser.z * 0.01 + 1)
                            tie_scale = 1 / (tie.z * 0.01 + 1)
                            
                            laser_x = WINDOW_WIDTH/2 + (laser.x - WINDOW_WIDTH/2) * laser_scale
                            laser_y = WINDOW_HEIGHT/2 + (laser.y - WINDOW_HEIGHT/2) * laser_scale
                            
                            tie_x = WINDOW_WIDTH/2 + (tie.x - WINDOW_WIDTH/2) * tie_scale
                            tie_y = WINDOW_HEIGHT/2 + (tie.y - WINDOW_HEIGHT/2) * tie_scale
                            
                            # Increase base hit box size significantly
                            base_hitbox_size = 50  # Increased from 35
                            scaled_hitbox = base_hitbox_size * tie_scale
                            
                            # More forgiving collision detection
                            distance = math.sqrt((laser_x - tie_x)**2 + (laser_y - tie_y)**2)
                            z_distance = abs(laser.z - tie.z)
                            
                            # Update the collision detection section
                            if distance < scaled_hitbox and z_distance < 70:
                                tie.hit = True
                                create_tie_explosion(tie.x, tie.y, tie.z)
                                player.add_score(SCORE_PER_TIE)
                                player.ties_destroyed += 1  # Increment destroyed count
                                if laser in lasers:
                                    lasers.remove(laser)
                                break

                # Update and draw explosions
                for explosion in explosions[:]:
                    if not explosion.update():
                        explosions.remove(explosion)
                    else:
                        explosion.draw(temp_surface)

                # Update TIE fighters
                for tie in tie_fighters[:]:
                    tie.move()
                    
                    # Check for collision with player if TIE is close
                    if not tie.hit and tie.z < 50:  # Only check when TIE is close
                        tie_scale = 1 / (tie.z * 0.01 + 1)
                        tie_x = WINDOW_WIDTH/2 + (tie.x - WINDOW_WIDTH/2) * tie_scale
                        tie_y = WINDOW_HEIGHT/2 + (tie.y - WINDOW_HEIGHT/2) * tie_scale
                        
                        # Calculate distance to player
                        distance = math.sqrt((tie_x - player.x)**2 + (tie_y - player.y)**2)
                        if distance < 30:  # Collision radius
                            player.take_damage(COLLISION_DAMAGE)
                            tie.hit = True
                            explosions.append(Explosion(tie.x, tie.y, tie.z))
                        
                    if not tie.is_visible() or tie.hit:
                        if tie in tie_fighters:
                            tie_fighters.remove(tie)

                # Handle TIE fighter shooting - only if game is still playing
                if player.game_state == GAME_STATE_PLAYING:
                    for tie in tie_fighters:
                        if tie.should_shoot():
                            enemy_lasers.append(EnemyLaser(tie.x, tie.y, tie.z))

                # Update enemy lasers
                for laser in enemy_lasers[:]:
                    laser.move()
                    if not laser.is_visible():  # Remove only when off screen
                        enemy_lasers.remove(laser)
                        continue
                    
                    # Check for collision with player (only when laser is near player)
                    if laser.z > -50 and laser.z < 50:  # Check collision only in this range
                        laser_scale = 1 / (laser.z * 0.01 + 1)
                        laser_x = WINDOW_WIDTH/2 + (laser.x - WINDOW_WIDTH/2) * laser_scale
                        laser_y = WINDOW_HEIGHT/2 + (laser.y - WINDOW_HEIGHT/2) * laser_scale
                        
                        distance = math.sqrt((laser_x - player.x)**2 + (laser_y - player.y)**2)
                        if distance < 20:
                            player.take_damage(HEALTH_DAMAGE)
                            enemy_lasers.remove(laser)

                # Drawing section
                screen.fill((0, 0, 0))
                temp_surface.fill((0, 0, 0))
                
                # Get screen shake offset
                shake_x, shake_y = player.get_shake_offset()
                
                # Draw game elements to temp surface
                draw_trench(temp_surface)
                draw_player(temp_surface, player)
                
                # Draw TIE fighters
                for tie in tie_fighters:
                    tie.draw(temp_surface)
                
                # Draw all lasers
                for laser in lasers[:]:
                    laser.draw(temp_surface)
                
                # Draw enemy lasers
                for laser in enemy_lasers:
                    laser.draw(temp_surface)
                
                # Draw explosions
                for explosion in explosions:
                    explosion.draw(temp_surface)
                
                # Draw powerups - moved here so they appear on screen
                for powerup in health_powerups:
                    powerup.draw(temp_surface)
                
                # Draw UI elements to temp_surface
                player.draw_health_bar(temp_surface)
                player.draw_score(temp_surface)
                player.draw_stats(temp_surface)
                player.draw_speed_indicator(temp_surface)
                
                # Draw targeting computer overlay
                draw_targeting_computer(temp_surface, player)
                
                # Apply all drawings to screen with shake
                screen.blit(temp_surface, (shake_x, shake_y))
                
                # Update shake effect - moved here to ensure it's updated every frame
                player.update_shake()

                # Get delta time for timer
                dt = clock.tick(60)
                
                # Handle end game states
                if player.game_state != GAME_STATE_PLAYING:
                    player.end_timer += 1
                    # Draw game elements first
                    temp_surface.fill((0, 0, 0))  # Clear temp surface
                    player.draw_end_game_message(temp_surface)
                    # Apply to screen with shake
                    screen.blit(temp_surface, (shake_x, shake_y))
                    
                    # Check for restart
                    if player.end_timer > 60:  # Wait a bit before allowing restart
                        keys = pygame.key.get_pressed()
                        if keys[K_SPACE]:
                            # Reset game state
                            SCROLL_SPEED = BASE_SCROLL_SPEED  # Reset speed
                            player = Player()
                            lasers = []
                            enemy_lasers = []
                            tie_fighters = []
                            explosions = []
                            health_powerups = []  # Also reset powerups
                            spawn_timer = 0
                            powerup_timer = 0

                # Update difficulty if game is still playing
                if player.game_state == GAME_STATE_PLAYING:
                    player.update_difficulty()
                    
                    # Update TIE fighter speeds based on new scroll speed
                    for tie in tie_fighters:
                        tie.speed = (SCROLL_SPEED + 1) * 1.1

                # Update and spawn health powerups
                if player.game_state == GAME_STATE_PLAYING:
                    powerup_timer += 1
                    if powerup_timer >= HEALTH_POWERUP_INTERVAL:
                        spawn_x = WINDOW_WIDTH/2 + random.randint(-int(WINDOW_WIDTH/4), int(WINDOW_WIDTH/4))
                        health_powerups.append(HealthPowerup(spawn_x, TIE_SPAWN_DISTANCE))
                        powerup_timer = 0
                    
                    # Update powerups
                    for powerup in health_powerups[:]:
                        powerup.move()
                        
                        # Check collection
                        if not powerup.collected and powerup.z < 50:
                            powerup_scale = 1 / (powerup.z * 0.01 + 1)
                            powerup_x = WINDOW_WIDTH/2 + (powerup.x - WINDOW_WIDTH/2) * powerup_scale
                            powerup_y = WINDOW_HEIGHT/2 + (powerup.y - WINDOW_HEIGHT/2) * powerup_scale
                            
                            distance = math.sqrt((powerup_x - player.x)**2 + 
                                               (powerup_y - player.y)**2)
                            
                            if distance < 30:
                                player.health = min(HEALTH_MAX, player.health + HEALTH_RESTORE_AMOUNT)
                                powerup.collected = True
                                # Add collection effect
                                for _ in range(10):  # Reduced from 12 to 10 particles
                                    angle = random.random() * 2 * math.pi
                                    dist = random.randint(10, 35)  # Slightly reduced spread
                                    x = player.x + math.cos(angle) * dist
                                    y = player.y + math.sin(angle) * dist
                                    explosions.append(Explosion(x, y, 0, size=25))  # Slightly smaller particles
                        
                        # Remove if passed player or collected
                        if powerup.z < -100 or powerup.collected:
                            health_powerups.remove(powerup)

                # Update display
                pygame.display.flip()
                await asyncio.sleep(0)  # Add this for smoother web performance

            except Exception as e:
                print(f"Error in game loop: {e}")
                running = False
                
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        pygame.quit()

# Modify the entry point
if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.run(main())
    else:
        # For desktop, use this
        asyncio.run(main()) 