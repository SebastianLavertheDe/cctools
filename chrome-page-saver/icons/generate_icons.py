#!/usr/bin/env python3
"""
Generate icon files for sPageSaver Chrome extension.
Requires: pip install Pillow
"""

def create_icon(size):
    """Create a simple icon with PIL/Pillow"""
    try:
        from PIL import Image, ImageDraw

        # Create image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw circle background (gradient effect with solid color)
        margin = size // 128
        draw.ellipse([margin, margin, size - margin, size - margin],
                     fill=(26, 115, 232, 255))

        # Draw document
        doc_margin = size // 3
        doc_size = size // 2
        draw.rounded_rectangle([doc_margin, size // 5, doc_margin + doc_size, size // 5 + doc_size],
                               radius=size // 32, fill=(255, 255, 255, 240))

        # Draw text lines
        line_y = size // 2 + size // 16
        for i in range(5):
            line_width = doc_size - size // 8 if i < 4 else doc_size - size // 5
            draw.rounded_rectangle([doc_margin + size // 16, line_y,
                                   doc_margin + size // 16 + line_width, line_y + size // 32],
                                  radius=size // 64, fill=(26, 115, 232, min(255, 180 - i * 30)))
            line_y += size // 16 + size // 64

        # Draw save badge (green circle)
        badge_size = size // 5
        badge_x = size - size // 4 - badge_size // 2
        badge_y = size - size // 4 - badge_size // 2
        draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
                     fill=(76, 175, 80, 255))

        # Draw floppy disk icon on badge
        floppy_size = badge_size // 2
        floppy_x = badge_x + (badge_size - floppy_size) // 2
        floppy_y = badge_y + (badge_size - floppy_size) // 2
        draw.rounded_rectangle([floppy_x, floppy_y, floppy_x + floppy_size, floppy_y + floppy_size * 0.7],
                               radius=max(1, size // 64), fill=(255, 255, 255, 255))
        draw.rounded_rectangle([floppy_x + floppy_size // 4, floppy_y + floppy_size * 0.7,
                               floppy_x + floppy_size * 0.75, floppy_y + floppy_size * 0.9],
                              radius=max(1, size // 64), fill=(255, 255, 255, 255))

        return img
    except ImportError:
        print("Pillow not installed. Run: pip install Pillow")
        return None

def main():
    import os

    print("Generating icons for sPageSaver...")

    for size in [16, 32, 48, 128]:
        icon = create_icon(size)
        if icon:
            filename = f'icon{size}.png'
            icon.save(filename)
            print(f"  Created {filename}")
        else:
            print(f"  Skipped {filename}")

    print("\nDone! Icons generated successfully.")

if __name__ == '__main__':
    main()
