import os
import tempfile

SYSTEM_TEMP = tempfile.gettempdir()
TEMP_DIR = os.path.join(SYSTEM_TEMP, "quran_reel_temp")
OUTPUT_DIR = os.path.join(SYSTEM_TEMP, "quran_reel_outputs")
FONT_ARABIC = "font.ttf"

# Ensure directories exist
for d in [TEMP_DIR, OUTPUT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

POPULAR_RECITERS = [
    ("ar.alafasy",          "Mishary Rashid Alafasy"),
    ("ar.abdurrahmaanas-sudais", "Abdurrahman As-Sudais"),
    ("ar.abdulbasitmurattal",   "Abdul Basit (Murattal)"),
    ("ar.husary",           "Mahmoud Khalil Al-Husary"),
    ("ar.minshawi",         "Mohamed Siddiq El-Minshawi"),
    ("ar.maaborali",        "Maher Al Muaiqly"),
    ("ar.ahmedajamy",       "Ahmed ibn Ali al-Ajamy"),
    ("ar.saaborali",        "Saad Al-Ghamdi"),
]
