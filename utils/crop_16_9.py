from PIL import Image
import sys
import os

def center_crop_16_9(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        
        # Target dimensions (Keep width, reduce height to match 16:9)
        # 16:9 = 1.777
        target_h = int(w * 9 / 16)
        
        if target_h > h:
            print(f"Skipping {image_path}: Image is too tall/narrow to crop to 16:9 (Width {w} needs Height {target_h}, but has {h})")
            # If too narrow, we might need to extend width, but let's assume square input (1024x1024) -> need 576 height. 576 < 1024. Safe.
            return

        # Calculate crop box
        top = (h - target_h) // 2
        bottom = top + target_h
        
        # Crop
        crop_img = img.crop((0, top, w, bottom))
        
        # Save overwrite
        crop_img.save(image_path)
        print(f"Successfully cropped {image_path} to {w}x{target_h} (16:9)")
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 crop_16_9.py <image_path>")
        sys.exit(1)
    
    center_crop_16_9(sys.argv[1])
