from PIL import Image, ImageDraw, ImageFont

def create_icon():
    """Create a simple icon for the SuperScribe application"""
    # Create a new image with transparent background
    size = 64
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Draw a circle
    margin = 2
    draw.ellipse(
        [(margin, margin), (size - margin, size - margin)],
        fill=(65, 105, 225)  # Royal blue
    )
    
    # Add a letter "S" in the middle
    try:
        # Try to load a font
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw the "S"
    text_width, text_height = draw.textsize("S", font=font) if hasattr(draw, 'textsize') else (20, 30)
    position = ((size - text_width) // 2, (size - text_height) // 2 - 2)
    draw.text(position, "S", fill=(255, 255, 255), font=font)
    
    # Save the icon
    icon_path = "superscribe_icon.png"
    icon.save(icon_path)
    
    return icon_path

if __name__ == "__main__":
    # Generate the icon if this script is run directly
    path = create_icon()
    print(f"Icon created at: {path}") 