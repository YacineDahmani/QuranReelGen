import os
import requests
import logging
import traceback
from typing import Optional
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ImageClip,
    VideoFileClip
)

from .config import FONT_ARABIC, OUTPUT_DIR, TEMP_DIR
from .utils import hex_to_rgb, get_cached_path, download_file, get_font
from .models import ReelRequest

# Reusable HTTP session
http_session = requests.Session()
http_session.headers.update({'User-Agent': 'QuranReelGen/1.0'})

def get_ayah_data(surah: int, ayah: int, reciter: str, include_translation: bool):
    """Fetches Audio, Arabic Text, and optionally English Translation."""
    logging.info(f"Fetching Surah {surah}, Ayah {ayah}...")

    audio_url = f"http://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{reciter}"
    text_url = f"http://api.alquran.cloud/v1/ayah/{surah}:{ayah}/quran-uthmani"
    
    data = {}
    try:
        audio_resp = http_session.get(audio_url, timeout=30).json()
        text_resp = http_session.get(text_url, timeout=30).json()

        if audio_resp.get("code") != 200 or text_resp.get("code") != 200:
            raise Exception(f"API Error for {surah}:{ayah}")

        data["audio_url"] = audio_resp["data"]["audio"]
        data["text"] = text_resp["data"]["text"]
        data["numberInSurah"] = text_resp["data"]["numberInSurah"]

        if include_translation:
            trans_url = f"http://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.sahih"
            trans_resp = http_session.get(trans_url, timeout=30).json()
            if trans_resp.get("code") == 200:
                data["translation"] = trans_resp["data"]["text"]
            else:
                data["translation"] = ""
        else:
            data["translation"] = ""

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        raise Exception(f"Network/API Error: {str(e)}")

    return data

def create_text_image(
    arabic_text: str, 
    english_text: Optional[str] = None, 
    ayah_number: Optional[int] = None,
    font_size: int = 70, 
    font_color: str = "#FFFFFF", 
    size=(1080, 1920),
    orientation: str = "vertical"
):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if ayah_number:
        arabic_text = f"{arabic_text} ({ayah_number})"

    configuration = {'delete_harakat': False}
    reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
    reshaped_text = reshaper.reshape(arabic_text)
    bidi_text = get_display(reshaped_text)

    font_ar = get_font(FONT_ARABIC, font_size)

    def wrap_text(text, font, max_w):
        lines = []
        words = text.split()
        curr_line = []
        for word in words:
            test_line = ' '.join(curr_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_w:
                curr_line.append(word)
            else:
                lines.append(' '.join(curr_line))
                curr_line = [word]
        if curr_line: lines.append(' '.join(curr_line))
        return lines

    max_width = size[0] - 150
    ar_lines = wrap_text(bidi_text, font_ar, max_width)

    en_lines = []
    font_en = None
    if english_text:
        try:
            font_en = get_font("arial.ttf", int(font_size * 0.4))
        except:
            try:
                font_en = get_font("C:/Windows/Fonts/arial.ttf", int(font_size * 0.4)) 
            except:
                font_en = ImageFont.load_default()
        
        en_lines = wrap_text(english_text, font_en, max_width)

    total_h = 0
    line_spacing = 20
    
    ar_heights = []
    for line in ar_lines:
        bbox = draw.textbbox((0, 0), line, font=font_ar)
        h = bbox[3] - bbox[1]
        ar_heights.append(h)
        total_h += h + line_spacing

    en_heights = []
    if english_text:
        total_h += 40 
        for line in en_lines:
            bbox = draw.textbbox((0, 0), line, font=font_en)
            h = bbox[3] - bbox[1]
            en_heights.append(h)
            total_h += h + 10

    current_y = (size[1] - total_h) // 2
    shadow_offset = 3
    shadow_color = (0, 0, 0, 200)

    for i, line in enumerate(ar_lines):
        bbox = draw.textbbox((0, 0), line, font=font_ar)
        w = bbox[2] - bbox[0]
        x = (size[0] - w) // 2
        draw.text((x + shadow_offset, current_y + shadow_offset), line, font=font_ar, fill=shadow_color)
        draw.text((x, current_y), line, font=font_ar, fill=font_color)
        current_y += ar_heights[i] + line_spacing

    if english_text:
        current_y += 20 
        for i, line in enumerate(en_lines):
            bbox = draw.textbbox((0, 0), line, font=font_en)
            w = bbox[2] - bbox[0]
            x = (size[0] - w) // 2
            draw.text((x + 2, current_y + 2), line, font=font_en, fill=shadow_color)
            draw.text((x, current_y), line, font=font_en, fill="#E2E8F0")
            current_y += en_heights[i] + 10

    return np.array(img)

def fetch_ayah_parallel(args):
    surah, ayah_num, reciter_id, include_translation = args
    try:
        data = get_ayah_data(surah, ayah_num, reciter_id, include_translation)
        audio_path = get_cached_path(data["audio_url"], "mp3")
        download_file(data["audio_url"], audio_path)
        data["audio_path"] = audio_path
        return ayah_num, data, None
    except Exception as e:
        return ayah_num, None, str(e)

def process_job(job_id: str, req: ReelRequest, jobs_dict: dict):
    try:
        jobs_dict[job_id]["status"] = "processing"
        jobs_dict[job_id]["progress"] = 0
        
        clips = []
        logging.info(f"Starting Job {job_id}")

        out_dir = req.output_dir if req.output_dir else OUTPUT_DIR
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        total_ayahs = req.ayah_end - req.ayah_start + 1
        if total_ayahs > req.max_ayahs:
            logging.warning(f"Capping to {req.max_ayahs} ayahs")
            req.ayah_end = req.ayah_start + req.max_ayahs - 1
            total_ayahs = req.max_ayahs

        video_width, video_height = (1920, 1080) if req.orientation == "horizontal" else (1080, 1920)
        
        # Background Setup
        bg_source_clip = None
        if req.bg_type == "video":
            if req.bg_value.startswith("http"):
                bg_path = get_cached_path(req.bg_value, "mp4")
                download_file(req.bg_value, bg_path)
                req.bg_value = bg_path
            
            if os.path.exists(req.bg_value):
                bg_source_clip = VideoFileClip(req.bg_value)
                if req.orientation == "horizontal":
                    bg_source_clip = bg_source_clip.resize(width=1920)
                    if bg_source_clip.h > 1080:
                        bg_source_clip = bg_source_clip.crop(y1=(bg_source_clip.h - 1080) // 2, width=1920, height=1080)
                else:
                    bg_source_clip = bg_source_clip.resize(height=1920)
                    if bg_source_clip.w > 1080:
                        bg_source_clip = bg_source_clip.crop(x1=(bg_source_clip.w - 1080) // 2, width=1080, height=1920)
            else:
                req.bg_type = "color"
                req.bg_value = "#000000"

        # Parallel fetch
        fetch_args = [(req.surah, i, req.reciter_id, req.include_translation) for i in range(req.ayah_start, req.ayah_end + 1)]
        ayah_data_map = {}
        with ThreadPoolExecutor(max_workers=min(total_ayahs, 20)) as executor:
            futures = {executor.submit(fetch_ayah_parallel, args): args[1] for args in fetch_args}
            completed = 0
            for future in as_completed(futures):
                num, data, err = future.result()
                if err: raise Exception(f"Ayah {num} fetch failed: {err}")
                ayah_data_map[num] = data
                completed += 1
                jobs_dict[job_id]["progress"] = int((completed / total_ayahs) * 50)
        
        # Parallel Image Generation
        image_gen_args = []
        for num in range(req.ayah_start, req.ayah_end + 1):
            data = ayah_data_map[num]
            arabic = req.custom_text if (req.custom_text and num == req.ayah_start) else data["text"]
            image_gen_args.append((arabic, data.get("translation"), data.get("numberInSurah"), req.font_size, req.font_color, (video_width, video_height), req.orientation))

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            text_images = list(executor.map(lambda x: create_text_image(*x), image_gen_args))
        
        jobs_dict[job_id]["progress"] = 70

        # Assembly
        for i, num in enumerate(range(req.ayah_start, req.ayah_end + 1)):
            data = ayah_data_map[num]
            audio_clip = AudioFileClip(data["audio_path"])
            duration = max(0, audio_clip.duration - 0.05)
            audio_clip = audio_clip.subclip(0, duration)
            
            if req.bg_type == "color":
                bg_clip = ColorClip(size=(video_width, video_height), color=hex_to_rgb(req.bg_value), duration=duration)
            else:
                bg_clip = bg_source_clip.loop(duration=duration) if bg_source_clip.duration < duration else bg_source_clip.subclip(0, duration)
                overlay = ColorClip(size=(video_width, video_height), color=(0,0,0), duration=duration).set_opacity(0.4)
                bg_clip = CompositeVideoClip([bg_clip, overlay])

            txt_clip = ImageClip(text_images[i]).set_duration(duration)
            clips.append(CompositeVideoClip([bg_clip, txt_clip]).set_audio(audio_clip))

        jobs_dict[job_id]["progress"] = 85
        final_video = concatenate_videoclips(clips, method="compose")
        output_filename = os.path.join(out_dir, f"output_{job_id}.mp4")
        
        final_video.write_videofile(
            output_filename, fps=req.fps, codec="libx264", audio_codec="aac",
            threads=os.cpu_count(), preset=req.video_quality, ffmpeg_params=["-movflags", "+faststart"],
            temp_audiofile=os.path.join(TEMP_DIR, f"temp_audio_{job_id}.m4a"), remove_temp=True
        )
        
        jobs_dict[job_id].update({"status": "completed", "progress": 100, "output_file": output_filename})
        # Note: result_url should probably be set by the API layer since it depends on the host/port

    except Exception as e:
        logging.error(traceback.format_exc())
        jobs_dict[job_id].update({"status": "failed", "error": str(e)})
