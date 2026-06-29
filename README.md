# STIG Generator

A modern graphical desktop application built with Python and CustomTkinter to create, edit, manage, import, and export XCCDF-compliant STIG XML files.

## Installation & Setup

1. **Clone/Download the repository**
2. Ensure you have Python 3.8+ installed.
3. Install dependencies inside the virtual environment:
   ```bash
   source venv/bin/activate
   pip install customtkinter jinja2
   ```

## Running the Application

### Option 1: Using the helper script
Run the provided launcher script (recommended):
```bash
./run.sh
```

### Option 2: Activating the virtual environment
Activate the environment first:
```bash
source venv/bin/activate
python main.py
```

### Option 3: Direct execution
Run via the virtual environment path directly:
```bash
./venv/bin/python main.py
```