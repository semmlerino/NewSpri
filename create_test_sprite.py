#!/usr/bin/env python3
"""
Create a test sprite sheet for demonstrating border detection
"""

from PIL import Image, ImageDraw
import numpy as np

def create_test_sprite_sheet():
    """Create a test sprite sheet with multiple sprites for border detection testing"""
    
    # Create a 256x256 canvas with transparent background
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define sprite positions (64x64 sprites with 8px margins)
    sprite_size = 64
    margin = 8
    
    sprites_data = [
        # First row
        {"pos": (margin, margin), "color": (255, 100, 100, 255), "shape": "rectangle"},
        {"pos": (margin + sprite_size + margin, margin), "color": (100, 255, 100, 255), "shape": "circle"},
        {"pos": (margin + 2*(sprite_size + margin), margin), "color": (100, 100, 255, 255), "shape": "triangle"},
        
        # Second row
        {"pos": (margin, margin + sprite_size + margin), "color": (255, 255, 100, 255), "shape": "diamond"},
        {"pos": (margin + sprite_size + margin, margin + sprite_size + margin), "color": (255, 100, 255, 255), "shape": "cross"},
        {"pos": (margin + 2*(sprite_size + margin), margin + sprite_size + margin), "color": (100, 255, 255, 255), "shape": "star"},
    ]
    
    # Draw sprites
    for sprite in sprites_data:
        x, y = sprite["pos"]
        color = sprite["color"]
        shape = sprite["shape"]
        
        if shape == "rectangle":
            draw.rectangle([x, y, x + sprite_size - 1, y + sprite_size - 1], fill=color)
        elif shape == "circle":
            draw.ellipse([x, y, x + sprite_size - 1, y + sprite_size - 1], fill=color)
        elif shape == "triangle":
            # Draw triangle
            points = [
                (x + sprite_size // 2, y),
                (x, y + sprite_size - 1),
                (x + sprite_size - 1, y + sprite_size - 1)
            ]
            draw.polygon(points, fill=color)
        elif shape == "diamond":
            # Draw diamond
            points = [
                (x + sprite_size // 2, y),
                (x + sprite_size - 1, y + sprite_size // 2),
                (x + sprite_size // 2, y + sprite_size - 1),
                (x, y + sprite_size // 2)
            ]
            draw.polygon(points, fill=color)
        elif shape == "cross":
            # Draw cross
            thickness = sprite_size // 4
            # Horizontal bar
            draw.rectangle([x, y + sprite_size//2 - thickness//2, 
                          x + sprite_size - 1, y + sprite_size//2 + thickness//2], fill=color)
            # Vertical bar
            draw.rectangle([x + sprite_size//2 - thickness//2, y, 
                          x + sprite_size//2 + thickness//2, y + sprite_size - 1], fill=color)
        elif shape == "star":
            # Draw simple 5-point star
            center_x, center_y = x + sprite_size // 2, y + sprite_size // 2
            outer_radius = sprite_size // 2 - 4
            inner_radius = outer_radius // 2
            
            points = []
            for i in range(10):
                angle = i * np.pi / 5
                if i % 2 == 0:
                    radius = outer_radius
                else:
                    radius = inner_radius
                px = center_x + radius * np.cos(angle - np.pi/2)
                py = center_y + radius * np.sin(angle - np.pi/2)
                points.append((px, py))
            
            draw.polygon(points, fill=color)
    
    # Save the test sprite sheet
    img.save('test_sprite_sheet.png')
    print("Test sprite sheet created: test_sprite_sheet.png")
    print(f"Sprites: {len(sprites_data)} sprites of {sprite_size}x{sprite_size}px each")
    print(f"Margins: {margin}px between sprites")
    print("Try loading this in the sprite viewer and use 'Detect Sprite Borders' button!")

if __name__ == "__main__":
    create_test_sprite_sheet()
