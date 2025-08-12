# Calculate and shows stage angle and angle between electron/ion beam and grid using a GUI
# Author : Tim Laugks - 26.11.2020
# Version: 31.07.2025
# CSSB Advanced Light and Fluorescence Microscopy (ALFM) Facility 
# Deutsches Elektronen-Synchrotron (DESY)

from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
import os
import sys
import tkinter as tk

# === PyInstaller-compatible resource path ===
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === Constants ===
STAGE_RANGE = (-192.5, 15)
EBEAM_RANGE = (-102.5, 105)
IBEAM_RANGE = (-154.5, 53)
IFLM_RANGE = (-105, 102.5)

# === GUI Setup ===
master = tk.Tk()
master.title("Arctis Angle Calculation")
master.geometry("470x680")

button_width = 18

img_label = Label(master)
img_label.grid(row=7, column=0, columnspan=4, sticky="w")

# === Tooltip-Klasse ===
class CreateToolTip(object):
    """Erstellt einen Tooltip für ein beliebiges Widget."""
    def __init__(self, widget, text='Tooltip text'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Fenster ohne Rahmen
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=5, ipady=2)

    def hidetip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# === Utility Functions ===
def clear_entries():
    for entry in [e1, e3, e4, e5]:
        entry.delete(0, END)

def validate_input(entry, value_range):
    try:
        value = float(entry.get())
    except ValueError:
        clear_entries()
        messagebox.showwarning("Invalid Input", f"Please enter a valid number between {value_range[0]} and {value_range[1]}")
        return None
    if not (value_range[0] <= value <= value_range[1]):
        clear_entries()
        messagebox.showwarning("Out of Range", f"Please enter a number between {value_range[0]} and {value_range[1]}")
        return None
    return value

def display_results(stage, ebeam, ibeam, iflm):
    for widget in [stage_label, ebeam_label, ibeam_label, iflm_label]:
        widget.config(text="")
    stage_label.config(text=f"{stage:.2f}")
    ebeam_label.config(text=f"{ebeam:.2f}")
    ibeam_label.config(text=f"{ibeam:.2f}")
    iflm_label.config(text=f"{iflm:.2f}")

def insert_image(angle, rotation):
    try:
        imagebig = Image.open(resource_path("images/autogridquerschnitt_gross.png")).rotate(angle, resample=Image.BICUBIC)
        imagesmall = Image.open(resource_path("images/geometry_caption.png"))
        mask_im = Image.open(resource_path("images/geometry.png"))
        imagebig.paste(imagesmall, mask_im)
        tkimage = ImageTk.PhotoImage(imagebig)
        img_label = Label(image=tkimage)
        img_label.image = tkimage
        img_label.grid(row=7, column=0, columnspan=4)
    except Exception as e:
        messagebox.showerror("Image Error", f"Error loading image: {e}")

    
# === Calculation Functions ===
def calculate_from_stage():
    stage = validate_input(e1, STAGE_RANGE)
    if stage is None: return
    ebeam = stage + 90
    ibeam = stage + 38
    iflm = -1 * (stage + 90)
    insert_image(stage, 180)
    display_results(stage, ebeam, ibeam, iflm)
    clear_entries()

def calculate_from_ebeam():
    ebeam = validate_input(e3, EBEAM_RANGE)
    if ebeam is None: return
    stage = ebeam - 90
    ibeam = ebeam - 52
    iflm = -ebeam
    insert_image(stage, 180)
    display_results(stage, ebeam, ibeam, iflm)
    clear_entries()

def calculate_from_ibeam():
    ibeam = validate_input(e4, IBEAM_RANGE)
    if ibeam is None: return
    stage = ibeam - 38
    ebeam = ibeam + 52
    iflm = -1 * (ibeam + 52)
    insert_image(stage, 180)
    display_results(stage, ebeam, ibeam, iflm)
    clear_entries()

def calculate_from_iflm():
    iflm = validate_input(e5, IFLM_RANGE)
    if iflm is None: return
    stage = -1 * (iflm + 90)
    ebeam = -iflm
    ibeam = -1 * (iflm + 52)
    insert_image(stage, 0)
    display_results(stage, ebeam, ibeam, iflm)
    e5.delete(0, END)

def handle_calculation():
    if e1.get():
        calculate_from_stage()
    elif e3.get():
        calculate_from_ebeam()
    elif e4.get():
        calculate_from_ibeam()
    elif e5.get():
        calculate_from_iflm()

def set_and_calculate(angle):
    e1.insert(0, angle)
    calculate_from_stage()

# === Layout ===
Label(master, text="Stage Angle / °").grid(row=0)
Label(master, text="Electron Beam /°").grid(row=1)
Label(master, text="Ion Beam /°").grid(row=2)
Label(master, text="iFLM /°").grid(row=3)

e1 = Entry(master, bg="white", width=7)
e3 = Entry(master, bg="white", width=7)
e4 = Entry(master, bg="white", width=7)
e5 = Entry(master, bg="white", width=7)

e1.grid(row=0, column=1)
e3.grid(row=1, column=1)
e4.grid(row=2, column=1)
e5.grid(row=3, column=1)

stage_label = Label(master, text="", bg="azure2", width=7)
ebeam_label = Label(master, text="", bg="azure2", width=7)
ibeam_label = Label(master, text="", bg="azure2", width=7)
iflm_label = Label(master, text="", bg="azure2", width=7)

stage_label.grid(row=0, column=2)
ebeam_label.grid(row=1, column=2)
ibeam_label.grid(row=2, column=2)
iflm_label.grid(row=3, column=2)

Button(master, text='Calculate', width=button_width, command=handle_calculation, bg="white")\
    .grid(row=0, column=3, padx=5, pady=4, sticky="w")

Button(master, text='iFLM', width=button_width, command=lambda: set_and_calculate(-180),
       bg="dim grey", fg="white")\
    .grid(row=1, column=3, padx=5, pady=2, sticky="w")

Button(master, text='Lamella Milling', width=button_width, command=lambda: set_and_calculate(-30),
       bg="dim grey", fg="white")\
    .grid(row=2, column=3, padx=5, pady=2, sticky="w")

Button(master, text='Perpendicular Milling', width=button_width, command=lambda: set_and_calculate(-128),
       bg="dim grey", fg="white")\
    .grid(row=3, column=3, padx=5, pady=2, sticky="w")

# Tooltips hinzufügen
CreateToolTip(e1, "Please enter angle in degrees (Stage Angle)")
CreateToolTip(e3, "Please enter angle in degrees (Electron Beam)")
CreateToolTip(e4, "Please enter angle in degrees (Ion Beam)")
CreateToolTip(e5, "Please enter angle in degrees (iFLM)")

# === Insert initial image ===
insert_image(0, 0)

# === Footer with logo and attribution ===
try:
    logo_img = Image.open(resource_path("images/cssb_logo.png"))
    logo_img = logo_img.resize((100, 34), Image.LANCZOS)
    logo_tk = ImageTk.PhotoImage(logo_img)
    logo_label = Label(master, image=logo_tk)
    logo_label.image = logo_tk
    logo_label.grid(row=8, column=0, sticky="w", padx=10, pady=10)
except Exception as e:
    print(f"Logo could not be loaded: {e}")

footer_text = "Created by Tim Laugks · July 2025"
Label(master, text=footer_text, font=("Arial", 8), fg="gray")\
    .grid(row=8, column=1, columnspan=3, sticky="w", padx=0, pady=10)

# === Run GUI ===
master.mainloop()


