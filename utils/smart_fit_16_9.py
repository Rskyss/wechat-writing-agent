from PIL import Image, ImageChops
import sys
import os

def smart_fit_16_9(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        
        # 1. Get background color from top-left pixel
        bg_color = img.getpixel((0, 0))
        
        # 2. Trim/Crop to content
        # Create a matching background image
        bg = Image.new(img.mode, img.size, bg_color)
        # Find difference
        diff = ImageChops.difference(img, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        # Get bounding box of content
        bbox = diff.getbbox()
        
        if bbox:
            content = img.crop(bbox)
        else:
            content = img # Fallback if empty
            
        # 3. Create target 16:9 canvas (e.g., base width on original or fixed high-res)
        # Let's say target height is 1080, width 1920 (Standard HD)
        target_h = 1080
        target_w = 1920
        new_canvas = Image.new("RGB", (target_w, target_h), bg_color)
        
        # 4. Resize content to fit target canvas with padding
        c_w, c_h = content.size
        # Scale factor to fit within target_w/target_h with some margin (e.g. 90%)
        scale_w = (target_w * 0.9) / c_w
        scale_h = (target_h * 0.9) / c_h
        scale = min(scale_w, scale_h)
        
        new_c_w = int(c_w * scale)
        new_c_h = int(c_h * scale)
        
        resized_content = content.resize((new_c_w, new_c_h), Image.Resampling.LANCZOS)
        
        # 5. Paste centered
        paste_x = (target_w - new_c_w) // 2
        paste_y = (target_h - new_c_h) // 2
        new_canvas.paste(resized_content, (paste_x, paste_y))
        
        # 6. Save
        new_canvas.save(image_path)
        print(f"Smart-fitted {image_path} to 16:9 (Scaled content x{scale:.2f})")
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 smart_fit_16_9.py <image_path>")
        sys.exit(1)
    
    smart_fit_16_9(sys.argv[1])
