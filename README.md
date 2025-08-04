# Arctis-Angle-calculator
GUI tool to calculate and visualize stage angle and angles between electron/ion beams and a Autoloader grid/Autogrid.

Created by **Tim Laugks**  
CSSB Advanced Light and Fluorescence Microscopy (ALFM) Facility  
Deutsches Elektronen-Synchrotron (DESY)  
**Version:** 31.07.2025



## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo

    (Optional) Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt




Usage

Run the GUI application:

python main.py

Replace main.py with the filename of your script if different.
Download Executable

Pre-built Windows executable (.exe) files are available in the Releases section of this repository for easy use without Python installation.




Requirements

    Python 3.x

    Pillow for image processing

    Tkinter (usually included with Python)


    

License

This project is licensed under the MIT License







Build the Executable Yourself (Optional)

If you'd like to generate the .exe manually:

    Install PyInstaller:

pip install pyinstaller

Run this command from the project folder:

pyinstaller --onefile ^
  --add-data "autogridquerschnitt_gross.png;." ^
  --add-data "geometry_caption.png;." ^
  --add-data "geometry.png;." ^
  --add-data "cssb_logo.png;." ^
  main.py

The .exe will appear in the dist/ folder.
