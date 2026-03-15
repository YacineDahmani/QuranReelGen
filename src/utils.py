import os
import requests
import logging
import hashlib
from PIL import Image, ImageFont
import urllib.request
from .config import TEMP_DIR, FONT_ARABIC

# Global font cache
font_cache = {}

def hex_to_rgb(hex_color: str):
    """Converts a hex color string to an RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

def get_cached_path(url: str, extension: str = "mp4") -> str:
    """Generates a consistent filename based on URL hash."""
    hash_object = hashlib.md5(url.encode())
    return os.path.join(TEMP_DIR, f"{hash_object.hexdigest()}.{extension}")

def download_file(url: str, filepath: str):
    """Downloads a file if it doesn't exist."""
    if os.path.exists(filepath):
        if os.path.getsize(filepath) > 0:
            logging.info(f"Using cached file: {filepath}")
            return
        else:
            logging.info(f"Cached file is empty, re-downloading: {filepath}")
            os.remove(filepath)

    logging.info(f"Downloading: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.pexels.com/'
    }
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=60)
        if r.status_code != 200:
            logging.error(f"Failed to download {url}, status: {r.status_code}")
            raise Exception(f"Failed to download {url}, status: {r.status_code}")
            
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
                
        if os.path.getsize(filepath) == 0:
            logging.error(f"Downloaded file is empty: {filepath}")
            raise Exception("Downloaded file is empty")
            
        logging.info(f"Download complete: {filepath} ({os.path.getsize(filepath)} bytes)")
            
    except Exception as e:
        logging.error(f"Download error for {url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        raise e

def get_font(font_path, size):
    key = (font_path, size)
    if key not in font_cache:
        try:
            font_cache[key] = ImageFont.truetype(font_path, size)
        except IOError:
            logging.warning(f"Font not found at {font_path}, using default")
            font_cache[key] = ImageFont.load_default()
    return font_cache[key]

def ensure_fonts():
    if not os.path.exists(FONT_ARABIC):
        logging.info("Downloading default Arabic font (Amiri)...")
        try:
            urllib.request.urlretrieve(
                "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf", 
                FONT_ARABIC
            )
        except Exception as e:
            logging.error(f"Failed to download Arabic font: {e}")
