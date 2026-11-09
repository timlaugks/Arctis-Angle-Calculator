# Arctis Angle Calculator

GUI tool to calculate and visualize stage angle and angles between electron/ion beams and an Autoloader grid (Autogrid) on the Thermo Fisher Arctis cryo-FIB/SEM.

Created by **Tim Laugks**  
CSSB Advanced Light and Fluorescence Microscopy (ALFM) Facility  
Deutsches Elektronen-Synchrotron (DESY)  
**Version:** 31.07.2025

> Previous version (v1.0, 2D Matplotlib-based): available in the [v1.0 Release](https://github.com/timlaugks/Arctis-Angle-Calculator/releases/tag/v1.0)

---

## What's New in v2.0

- **True 3D rendering** via vedo/VTK with a real OpenGL Z-buffer — no more rendering artefacts or incorrect occlusion
- **Interactive 3D view**: rotate with left-drag, zoom with scroll wheel or right-drag
- **3D Autogrid model**: load your own STL/OBJ/PLY file (`autogrid.stl`) for a realistic representation
- **Billboard labels**: beam labels always face the viewer, colored to match each beam
- **Preset positions**: quick buttons for iFLM, Lamella Milling, Perpendicular Milling and Home
- **Camera presets**: Iso, Side and Top views
- **Keyboard support**: ↑ / ↓ in any angle field steps by ±1°
- Redesigned GUI with clean card layout

---

## Installation

A pre-built Windows executable (.exe) is available in the [Releases](https://github.com/timlaugks/Arctis-Angle-Calculator/releases) section — no Python installation required.

### Run from source

Clone the repository:

```bash
git clone https://github.com/timlaugks/Arctis-Angle-Calculator.git
cd Arctis-Angle-Calculator
```

Install dependencies:

```bash
pip install numpy matplotlib pillow trimesh vedo
```

Optional (for mesh simplification of large STL files):

```bash
pip install fast-simplification
```

Run:

```bash
python arctisangle.py
```

### Requirements

- Python 3.9 or newer
- numpy
- matplotlib (for color utilities)
- Pillow
- trimesh
- vedo (includes VTK)
- fast-simplification *(optional)*
- Tkinter *(included with Python on Windows)*

---

## Usage

Enter any angle value and press **Enter** — all other angles update automatically.  
Drag the slider to tilt the stage interactively.  
Use the **View** buttons (Iso / Side / Top) to reset the camera.  
Left-drag rotates the 3D view, scroll wheel zooms.

### Optional files (place in the same folder as the script or .exe)

| File | Purpose |
|---|---|
| `autogrid.stl` | 3D model of the Autogrid (STL, OBJ, PLY, GLB supported) |
| `cssb_logo.png` | Logo shown in the footer |

If `autogrid.stl` is not found, a simple disc placeholder is shown instead.

---

## Build the Executable Yourself (Optional)

Install PyInstaller (version 6.x required):

```bash
pip install pyinstaller==6.3.0
```

Create a file `ArctisAngle.spec` in the project folder (see repository for the full spec file), then run:

```bash
pyinstaller ArctisAngle.spec
```

The `.exe` will appear in the `dist/` folder. Place `autogrid.stl` and `cssb_logo.png` next to it.

---

## Angle Definitions

| Field | Relation to stage angle *s* |
|---|---|
| Stage Angle | *s* |
| Electron Beam | *s* + 90° |
| Ion Beam | *s* + 38° |
| iFLM | −(*s* + 90°) |

Stage range: −195° to +9°

---

## License

This project is licensed under the MIT License.
