# Vehicle Record System

This project implements a campus/industrial vehicle record system using computer vision. It automates vehicle entry/exit logging by processing surveillance camera feeds.

## Features
- Real-time vehicle detection.
- License Plate Recognition (LPR).
- Automated logging of vehicle entries and exits.
- Database storage for records.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MrSubham08/vehicle-records-system.git
   cd vehicle-records-system
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows use:
   venv\Scripts\activate
   # On macOS/Linux use:
   # source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You might need to install specific dependencies for YOLO or OCR libraries separately, e.g., PyTorch/TensorFlow, Tesseract OCR engine)*

4. **Configure the system:**
   Edit `config/config.yaml` to set camera sources, database paths, detection zones, etc.

## Usage
To start the application, run:
```bash
python src/main.py
```