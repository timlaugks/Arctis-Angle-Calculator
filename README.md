# Arctis-Angle-calculator
GUI tool to calculate and visualize stage angle and angles between electron/ion beams and a Autoloader grid/Autogrid.

Created by **Tim Laugks**  
CSSB / ALFM Facility  
Deutsches Elektronen-Synchrotron (DESY)  
**Version:** 31.07.2025



## Installation

(Pre-built Windows executable (.exe) file is available in the Releases section of this repository for easy use without Python installation.)



Clone the repository:
```
   git clone https://github.com/your-username/your-repo.git
   
   cd your-repo
```

Install dependencies:

    pip install -r requirements.txt


Requirements

    Python 3.x

    Pillow for image processing

    Tkinter (usually included with Python)
    

Build the Executable Yourself (Optional)

If you'd like to generate the .exe manually:

Install PyInstaller:
```
pip install pyinstaller
```

Run this command from the project folder:
```
pyinstaller --onefile ^
  --add-data "images/autogridquerschnitt_gross.png;." ^
  --add-data "images/geometry_caption.png;." ^
  --add-data "images/geometry.png;." ^
  --add-data "images/cssb_logo.png;." ^
  arctisangle.py
```
The .exe will appear in the dist/ folder


## Usage

Run the GUI application:

```arctisangle.py```




  

## License

This project is licensed under the MIT License
