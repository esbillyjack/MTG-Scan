import pygame
import sys

# Initialize pygame
pygame.init()

# Create a simple window
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Test Window - Press any key to exit")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Font
font = pygame.font.Font(None, 36)

print("Test window should appear. Press any key to close.")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            running = False
    
    # Clear screen
    screen.fill(BLACK)
    
    # Draw test text
    text = font.render("Test Window - Press any key to exit", True, WHITE)
    text_rect = text.get_rect(center=(400, 300))
    screen.blit(text, text_rect)
    
    # Draw a red circle
    pygame.draw.circle(screen, RED, (400, 200), 50)
    
    # Update display
    pygame.display.flip()

pygame.quit()
print("Test window closed.") 