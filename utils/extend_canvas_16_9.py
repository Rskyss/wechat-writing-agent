from PIL import Image
import sys
import os

def extend_canvas_16_9(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        target_aspect = 16 / 9
        current_aspect = w / h

        if abs(current_aspect - target_aspect) < 0.1:
            print(f"Skipping {image_path}: Already close to 16:9 aspect ratio.")
            return

        # Calculate new width to satisfy 16:9
        new_w = int(h * target_aspect)
        
        # Get background color from top-left pixel
        bg_color = img.getpixel((0, 0))
        
        # Create new canvas
        new_img = Image.new("RGB", (new_w, h), bg_color)
        
        # Paste original image in center
        paste_x = (new_w - w) // 2
        new_img.paste(img, (paste_x, 0))
        
        # Save overwrite
        new_img.save(image_path)
        print(f"Successfully resized {image_path} to {new_w}x{h} (16:9)")
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extend_canvas_16_9.py <image_path>")
        sys.exit(1)
    
    extend_canvas_16_9(sys.argv[1])
