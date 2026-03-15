from pydantic import BaseModel
from typing import Optional

class ReelRequest(BaseModel):
    surah: int
    ayah_start: int
    ayah_end: int
    reciter_id: str
    bg_type: str = "color"
    bg_value: str = "#000000"
    custom_text: Optional[str] = None 
    font_size: int = 100
    font_color: str = "#FFFFFF"
    include_translation: bool = False
    orientation: str = "vertical"
    output_dir: Optional[str] = None
    max_ayahs: int = 50
    fps: int = 24
    video_quality: str = "ultrafast"
