# Quran Reel Generator

A powerful Python tool to generate high-quality Islamic reels (vertical or horizontal) featuring Quranic verses, synchronized audio recitations, and optional English translations. It can be used as a **REST API** (FastAPI) or as a **Command Line Interface (CLI)**.

## ✨ Features

- ** Interactive CLI**: A clean, menu-driven dashboard for configuring reels before generation.
- **REST API**: Built with FastAPI for easy integration with web or mobile apps.
- **Arabic Rendering**: Proper Uthmani script rendering with reshaping and BiDi support.
- **Dynamic Backgrounds**: Use solid colors or high-quality video backgrounds (URLs or local files).
- **Parallel Processing**: Multi-threaded generation for high performance.
- **Translation Support**: Optional English translations shown alongside Arabic.

## 🛠️ Prerequisites

- **Python 3.8+**
- **FFmpeg**: Required for video processing.
  - Windows: [Download from Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (add to PATH).

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/QuranReelGen.git
   cd QuranReelGen
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 📂 Project Structure

- `main.py`: Entry point for the application.
- `src/`: Core package containing:
  - `api.py`: FastAPI routes and server logic.
  - `cli.py`: Interactive and flag-based CLI interface.
  - `core.py`: Video generation and data fetching logic.
  - `models.py`: Pydantic models for validation.
  - `config.py`: Configuration and paths.
  - `utils.py`: Helper functions (fonts, colors, downloads).

## 💻 Usage

### 1. Interactive CLI (Default)
Run the clean, menu-driven interface:
```bash
python main.py
```
This mode lets you verify and change all settings (Surah, Reciter, Background, etc.) from a dashboard before starting the generation.

### 2. REST API
Start the FastAPI server:
```bash
python main.py --api
```
Server runs on `http://localhost:8001`. Use the `/generate` endpoint to start jobs.

### 3. Command Line (Direct)
Generate a reel directly with flags:
```bash
python main.py --surah 1 --ayah-start 1 --ayah-end 7 --reciter ar.alafasy
```

## 📜 Credits

- **Quran API**: [AlQuran.cloud](https://alquran.cloud/api)
- **Fonts**: Amiri Font (SIL Open Font License)
- **Recitations**: Provided by various reciters via AlQuran.cloud.
