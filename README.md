# Vehicle Record System

This project implements a campus/industrial vehicle record system using computer vision. It automates vehicle entry/exit logging by processing surveillance camera feeds.

## Features

*   Real-time vehicle detection.
*   License Plate Recognition (LPR).
*   Automated logging of vehicle entries and exits.
*   Database storage for records.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your_username/vehicle-record-system.git
    cd vehicle-record-system
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You might need to install specific dependencies for YOLO or OCR libraries separately, e.g., PyTorch/TensorFlow, Tesseract OCR engine)*

4.  **Configure the system:**
    *   Edit `config/config.yaml` to set camera sources, database paths, detection zones, etc.

## Usage

```bash
python src/main.py