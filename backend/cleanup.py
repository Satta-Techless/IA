import os
import time

def cleanup_old_files(days=7):
    folders = ["posters", "image_cache", "deep_dive_images"]
    now = time.time()
    for folder in folders:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                path = os.path.join(folder, f)
                if os.path.isfile(path):
                    age = (now - os.path.getctime(path)) / 86400
                    if age > days:
                        os.remove(path)
                        print(f"Removed {path}")