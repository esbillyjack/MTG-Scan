#!/usr/bin/env python3
"""
Main entry point for Magic Card Scanner - Railway Deployment
"""
import pygame
import sys
import random
import math
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (100, 150, 255)

# Game states
TITLE_SCREEN = "title"
CHARACTER_SELECT = "character_select"
PLAYING = "playing"
GAME_OVER = "game_over"

class Object:
    """Base class for all game objects"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
    
    def update(self):
        pass
    
    def draw(self, screen):
        pass
    
    def collides_with(self, other):
        return self.rect.colliderect(other.rect)

class player(Object):
    """Player aircraft class"""
    def __init__(self, x, y, character="rex"):
        super().__init__(x, y, 60, 40)
        self.character = character
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.bullets = []
        self.last_shot = 0
        self.shot_delay = 200  # milliseconds
        self.invulnerable = False
        self.invulnerable_timer = 0
        
        # Character-specific stats
        if character == "rex":
            self.speed = 5
            self.shot_delay = 200
        elif character == "luna":
            self.speed = 6
            self.shot_delay = 150
        elif character == "paco":
            self.speed = 4
            self.shot_delay = 100
    
    def update(self):
        # Handle input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
        
        # Keep player on screen
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
        
        # Update rect
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.y < -10:
                self.bullets.remove(bullet)
        
        # Update invulnerability
        if self.invulnerable:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
    
    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shot_delay:
            new_bullet = bullet(self.x + self.width // 2, self.y)
            self.bullets.append(new_bullet)
            self.last_shot = current_time
    
    def take_damage(self, damage):
        if not self.invulnerable:
            self.health -= damage
            self.invulnerable = True
            self.invulnerable_timer = 60  # 1 second at 60 FPS
            return True
        return False
    
    def draw(self, screen):
        # Draw player (simple rectangle for now)
        color = WHITE if not self.invulnerable else (255, 255, 255, 128)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)

class bullet(Object):
    """Bullet class"""
    def __init__(self, x, y):
        super().__init__(x, y, 4, 10)
        self.speed = 10
    
    def update(self):
        self.y -= self.speed
        self.rect.y = self.y
    
    def draw(self, screen):
        pygame.draw.rect(screen, YELLOW, self.rect)

class enemy(Object):
    """Enemy aircraft class"""
    def __init__(self, x, y, enemy_type="cat"):
        super().__init__(x, y, 40, 30)
        self.enemy_type = enemy_type
        self.speed = random.randint(2, 5)
        self.health = 20
        self.max_health = 20
        
        if enemy_type == "boss":
            self.width = 80
            self.height = 60
            self.rect = pygame.Rect(x, y, self.width, self.height)
            self.health = 100
            self.max_health = 100
            self.speed = 1
    
    def update(self):
        self.y += self.speed
        self.rect.y = self.y
    
    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0
    
    def draw(self, screen):
        # Draw enemy (simple rectangle for now)
        color = RED if self.enemy_type == "boss" else (255, 100, 100)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

class game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Aces Pup - Dog Fighters vs Cat Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.state = TITLE_SCREEN
        self.selected_character = "rex"
        self.available_characters = ["rex"]  # Only Rex is available initially
        
        # Game objects
        self.player = None
        self.enemies = []
        self.score = 0
        self.level = 1
        self.enemy_spawn_timer = 0
        self.boss_spawn_timer = 0
        
        # Load assets
        self.load_assets()
        
        # Music
        self.music_playing = False
        self.music_timer = 0
        self.music_loop_delay = 30000  # 30 seconds
        
    def load_assets(self):
        """Load game assets"""
        try:
            # Load logo
            self.logo = pygame.image.load("art_dump/aces_logo.png")
            self.logo = pygame.transform.scale(self.logo, (400, 200))
            
            # Load character selection images
            self.rex_select = pygame.image.load("art_dump/rex_select.png")
            self.rex_select = pygame.transform.scale(self.rex_select, (200, 150))
            
            self.luna_select = pygame.image.load("art_dump/luna_select.png")
            self.luna_select = pygame.transform.scale(self.luna_select, (200, 150))
            
            self.paco_select = pygame.image.load("art_dump/paco_select.png")
            self.paco_select = pygame.transform.scale(self.paco_select, (200, 150))
            
            # Load music
            pygame.mixer.music.load("art_dump/groove.wav")
            
        except pygame.error as e:
            print(f"Error loading assets: {e}")
            # Create placeholder assets
            self.logo = pygame.Surface((400, 200))
            self.logo.fill(BLUE)
            self.rex_select = pygame.Surface((200, 150))
            self.rex_select.fill(GREEN)
            self.luna_select = pygame.Surface((200, 150))
            self.luna_select.fill(GRAY)
            self.paco_select = pygame.Surface((200, 150))
            self.paco_select.fill(GRAY)
    
    def start_music(self):
        """Start background music with looping behavior"""
        if not self.music_playing:
            pygame.mixer.music.play()
            self.music_playing = True
            self.music_timer = pygame.time.get_ticks()
    
    def update_music(self):
        """Update music looping behavior"""
        if self.music_playing:
            current_time = pygame.time.get_ticks()
            if current_time - self.music_timer > self.music_loop_delay:
                pygame.mixer.music.play()
                self.music_timer = current_time
    
    def stop_music(self):
        """Stop and fade out music"""
        if self.music_playing:
            pygame.mixer.music.fadeout(1000)
            self.music_playing = False
    
    def spawn_enemy(self):
        """Spawn a new enemy"""
        x = random.randint(0, SCREEN_WIDTH - 40)
        enemy_type = "cat"
        if random.random() < 0.1:  # 10% chance for boss
            enemy_type = "boss"
            x = random.randint(0, SCREEN_WIDTH - 80)
        
        new_enemy = enemy(x, -50, enemy_type)
        self.enemies.append(new_enemy)
    
    def update_enemies(self):
        """Update all enemies"""
        for enemy in self.enemies[:]:
            enemy.update()
            if enemy.y > SCREEN_HEIGHT:
                self.enemies.remove(enemy)
    
    def check_collisions(self):
        """Check for collisions between game objects"""
        if not self.player:
            return
        
        # Player bullets vs enemies
        for bullet in self.player.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.collides_with(enemy):
                    if enemy.take_damage(20):
                        self.enemies.remove(enemy)
                        self.score += 10 if enemy.enemy_type != "boss" else 50
                    if bullet in self.player.bullets:
                        self.player.bullets.remove(bullet)
                    break
        
        # Player vs enemies
        for enemy in self.enemies[:]:
            if self.player.collides_with(enemy):
                if self.player.take_damage(20):
                    if enemy.enemy_type == "boss":
                        self.enemies.remove(enemy)
                        self.score += 50
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
    
    def draw_title_screen(self):
        """Draw the title screen"""
        self.screen.fill(BLACK)
        
        # Draw logo
        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(self.logo, logo_rect)
        
        # Draw title text
        title_text = self.font.render("ACES PUP", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(title_text, title_rect)
        
        subtitle_text = self.small_font.render("Dog Fighters vs Cat Invaders", True, LIGHT_BLUE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 380))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw instructions
        instruction_text = self.small_font.render("Press SPACE to start", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Draw character info
        char_text = self.small_font.render("Choose your dog ace pilot!", True, YELLOW)
        char_rect = char_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(char_text, char_rect)
    
    def draw_character_select(self):
        """Draw the character selection screen"""
        self.screen.fill(BLACK)
        
        # Draw title
        title_text = self.font.render("Choose Your Pilot", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw character boxes
        characters = [
            ("rex", "Rex the Beagle", self.rex_select, GREEN),
            ("luna", "Luna the Dachshund", self.luna_select, GRAY),
            ("paco", "Paco the Chihuahua", self.paco_select, GRAY)
        ]
        
        for i, (char_id, name, image, color) in enumerate(characters):
            x = 200 + i * 300
            y = 250
            
            # Draw character box
            box_rect = pygame.Rect(x - 10, y - 10, 220, 200)
            pygame.draw.rect(self.screen, color, box_rect)
            pygame.draw.rect(self.screen, WHITE, box_rect, 3)
            
            # Draw character image
            image_rect = image.get_rect(center=(x + 100, y + 75))
            self.screen.blit(image, image_rect)
            
            # Draw character name
            name_text = self.small_font.render(name, True, WHITE)
            name_rect = name_text.get_rect(center=(x + 100, y + 160))
            self.screen.blit(name_text, name_rect)
            
            # Draw selection indicator
            if char_id == self.selected_character:
                select_rect = pygame.Rect(x - 15, y - 15, 230, 210)
                pygame.draw.rect(self.screen, YELLOW, select_rect, 5)
            
            # Draw availability status
            if char_id not in self.available_characters:
                coming_soon_text = self.small_font.render("COMING SOON", True, RED)
                coming_soon_rect = coming_soon_text.get_rect(center=(x + 100, y + 180))
                self.screen.blit(coming_soon_text, coming_soon_rect)
        
        # Draw instructions
        instruction_text = self.small_font.render("Use LEFT/RIGHT to select, SPACE to confirm", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Draw character stats
        if self.selected_character == "rex":
            stats_text = "Speed: 5 | Fire Rate: Medium | Health: 100"
        elif self.selected_character == "luna":
            stats_text = "Speed: 6 | Fire Rate: Fast | Health: 100"
        elif self.selected_character == "paco":
            stats_text = "Speed: 4 | Fire Rate: Very Fast | Health: 100"
        
        stats_surface = self.small_font.render(stats_text, True, LIGHT_BLUE)
        stats_rect = stats_surface.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(stats_surface, stats_rect)
    
    def draw_game(self):
        """Draw the game screen"""
        self.screen.fill(BLACK)
        
        # Draw player
        if self.player:
            self.player.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
    
    def draw_ui(self):
        """Draw the game UI"""
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (10, 50))
        
        # Draw health bar
        if self.player:
            health_text = self.font.render(f"Health: {self.player.health}", True, WHITE)
            self.screen.blit(health_text, (10, 90))
            
            # Health bar
            bar_width = 200
            bar_height = 20
            health_percentage = self.player.health / self.player.max_health
            health_width = int(bar_width * health_percentage)
            
            pygame.draw.rect(self.screen, RED, (10, 130, bar_width, bar_height))
            pygame.draw.rect(self.screen, GREEN, (10, 130, health_width, bar_height))
            pygame.draw.rect(self.screen, WHITE, (10, 130, bar_width, bar_height), 2)
    
    def draw_game_over(self):
        """Draw the game over screen"""
        self.screen.fill(BLACK)
        
        # Draw game over text
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Draw final score
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(score_text, score_rect)
        
        # Draw instructions
        restart_text = self.small_font.render("Press SPACE to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = self.small_font.render("Press ESC for main menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, 430))
        self.screen.blit(menu_text, menu_rect)
    
    def handle_title_events(self, event):
        """Handle events on title screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.state = CHARACTER_SELECT
                self.start_music()
    
    def handle_character_select_events(self, event):
        """Handle events on character select screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if self.selected_character == "rex":
                    self.selected_character = "paco"
                elif self.selected_character == "luna":
                    self.selected_character = "rex"
                elif self.selected_character == "paco":
                    self.selected_character = "luna"
            elif event.key == pygame.K_RIGHT:
                if self.selected_character == "rex":
                    self.selected_character = "luna"
                elif self.selected_character == "luna":
                    self.selected_character = "paco"
                elif self.selected_character == "paco":
                    self.selected_character = "rex"
            elif event.key == pygame.K_SPACE:
                if self.selected_character in self.available_characters:
                    self.start_game()
    
    def handle_game_events(self, event):
        """Handle events during gameplay"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.player:
                    self.player.shoot()
            elif event.key == pygame.K_ESCAPE:
                self.state = TITLE_SCREEN
                self.stop_music()
    
    def handle_game_over_events(self, event):
        """Handle events on game over screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.start_game()
            elif event.key == pygame.K_ESCAPE:
                self.state = TITLE_SCREEN
                self.stop_music()
    
    def start_game(self):
        """Start a new game"""
        self.player = player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, self.selected_character)
        self.enemies = []
        self.score = 0
        self.level = 1
        self.enemy_spawn_timer = 0
        self.boss_spawn_timer = 0
        self.state = PLAYING
    
    def update_game(self):
        """Update game logic"""
        if not self.player:
            return
        
        # Update player
        self.player.update()
        
        # Spawn enemies
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer > 60:  # Spawn every second
            self.spawn_enemy()
            self.enemy_spawn_timer = 0
        
        # Update enemies
        self.update_enemies()
        
        # Check collisions
        self.check_collisions()
        
        # Check game over
        if self.player.health <= 0:
            self.state = GAME_OVER
            self.stop_music()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == TITLE_SCREEN:
                    self.handle_title_events(event)
                elif self.state == CHARACTER_SELECT:
                    self.handle_character_select_events(event)
                elif self.state == PLAYING:
                    self.handle_game_events(event)
                elif self.state == GAME_OVER:
                    self.handle_game_over_events(event)
            
            # Update music
            self.update_music()
            
            # Update game state
            if self.state == PLAYING:
                self.update_game()
            
            # Draw current state
            if self.state == TITLE_SCREEN:
                self.draw_title_screen()
            elif self.state == CHARACTER_SELECT:
                self.draw_character_select()
            elif self.state == PLAYING:
                self.draw_game()
            elif self.state == GAME_OVER:
                self.draw_game_over()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game_instance = game()
    game_instance.run() 