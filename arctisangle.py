# Calculate and shows stage angle and angle between electron/ion beam and grid using a GUI
# Author : Tim Laugks - 26.11.2020
# Version: 09.11.2026  (3D view, redesigned GUI)
# CSSB Advanced Light and Fluorescence Microscopy (ALFM) Facility
# Deutsches Elektronen-Synchrotron (DESY)
#
# Benoetigt: pip install numpy matplotlib pillow trimesh vedo

import os
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

import numpy as np
from PIL import Image, ImageTk
import vtk
from vtkmodules.util.numpy_support import vtk_to_numpy
import vedo
from vedo import Plotter, Mesh, Cylinder, Cone

# =============================================================================
# Einstellungen
# =============================================================================
STAGE_RANGE = (-195, 9)

LABELS = {"stage": "Stage Angle", "ebeam": "Electron Beam",
          "ibeam": "Ion Beam",    "iflm":  "iFLM"}
COLORS = {"stage": "#4b5563", "ebeam": "#e4572e",
          "ibeam": "#2f6fed", "iflm":  "#1fa463"}

BEAMS   = {"ebeam": 0, "ibeam": 52, "iflm": 180}
PRESETS = [("iFLM", -180), ("Lamella Milling", -30),
           ("Perpendicular Milling", -128), ("Home", 0)]
VIEWS   = {"Iso": (20, -60), "Side": (0, -90), "Top": (90, -90)}

MODEL_FILE     = "autogrid.stl"
MODEL_ROTATION = (0, 180, 90)
MODEL_COLOR    = "#d9a441"
MAX_FACES      = 8000

GRID_RADIUS          = 1.0
GRID_DIAMETER_MM     = 3.0
BEAM_POINT_OFFSET_MM = 0.1
BEAM_LENGTH          = 1.4
LABEL_FACTOR         = 1.62   # Abstand der Beschriftung vom Ursprung
LABEL_SCALE          = 0.15   # Schriftgroesse
SHAFT_RADIUS         = 0.022
HEAD_RADIUS          = 0.07
HEAD_LENGTH          = 0.22
BEAM_TIP_OFFSET      = 0.06   # Pfeilspitzen enden leicht versetzt vom Ursprung

UI_BG    = "#eef1f5"
CARD_BG  = "#ffffff"
PLOT_BG  = (240, 244, 248)

RENDER_W = 580
RENDER_H = 580


# =============================================================================
# Winkelberechnung
# =============================================================================
def angles_from_stage(s):
    return {"stage": s, "ebeam": s + 90, "ibeam": s + 38, "iflm": -(s + 90)}


STAGE_FROM = {
    "stage": lambda v: v,
    "ebeam": lambda v: v - 90,
    "ibeam": lambda v: v - 38,
    "iflm":  lambda v: -(v + 90),
}


def _field_range(key):
    ends = [angles_from_stage(s)[key] for s in STAGE_RANGE]
    return min(ends), max(ends)


FIELD_RANGE = {k: _field_range(k) for k in LABELS}


# =============================================================================
# Hilfs-Funktionen
# =============================================================================
def _hex_to_rgb(hexcol):
    h = hexcol.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def make_follower_label(line1, line2, position, color_rgb, scale, camera):
    """
    Erstellt einen zweizelligen Billboard-Text (vtkFollower) der sich immer
    zur Kamera dreht. Zentriert um 'position'.
    Gibt eine Liste von zwei vtkFollower-Actors zurueck (eine pro Zeile).
    """
    actors = []
    line_gap = scale * 1.4   # vertikaler Abstand der Zeilen

    for i, line in enumerate([line1, line2]):
        if not line:
            continue
        vt = vtk.vtkVectorText()
        vt.SetText(line)
        vt.Update()

        bounds = vt.GetOutput().GetBounds()
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2

        tf = vtk.vtkTransformFilter()
        tr = vtk.vtkTransform()
        # Zentrieren + Zeile 0 oben, Zeile 1 unten
        y_offset = line_gap * 0.5 if i == 0 else -line_gap * 0.5
        tr.Translate(-cx, -cy + y_offset / scale, 0)
        tf.SetTransform(tr)
        tf.SetInputConnection(vt.GetOutputPort())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(tf.GetOutputPort())

        follower = vtk.vtkFollower()
        follower.SetMapper(mapper)
        follower.SetCamera(camera)
        follower.SetScale(scale)
        follower.GetProperty().SetColor(*color_rgb)
        follower.SetPosition(*position)
        actors.append(follower)

    return actors


# =============================================================================
# 3D-Modell laden
# =============================================================================
def _rot_matrix(rx, ry, rz):
    rx, ry, rz = np.radians([rx, ry, rz])
    Rx = np.array([[1,0,0],[0,np.cos(rx),-np.sin(rx)],[0,np.sin(rx),np.cos(rx)]])
    Ry = np.array([[np.cos(ry),0,np.sin(ry)],[0,1,0],[-np.sin(ry),0,np.cos(ry)]])
    Rz = np.array([[np.cos(rz),-np.sin(rz),0],[np.sin(rz),np.cos(rz),0],[0,0,1]])
    return Rz @ Ry @ Rx


def _placeholder_verts_faces(n=72):
    th    = np.linspace(0, 2*np.pi, n, endpoint=False)
    rim   = GRID_RADIUS * np.c_[np.cos(th), np.sin(th), np.zeros(n)]
    verts = np.vstack([[0, 0, 0], rim])
    faces = np.array([[0, 1+i, 1+(i+1)%n] for i in range(n)])
    return verts, faces


def load_model():
    if not os.path.exists(MODEL_FILE):
        print(f"'{MODEL_FILE}' nicht gefunden – Scheibe als Platzhalter.")
        return _placeholder_verts_faces()
    try:
        import trimesh
        mesh = trimesh.load(MODEL_FILE, force="mesh")
    except Exception as e:
        print(f"Modell konnte nicht geladen werden: {e}")
        return _placeholder_verts_faces()

    if len(mesh.faces) > MAX_FACES:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=MAX_FACES)
        except Exception:
            print(f"Modell hat {len(mesh.faces)} Dreiecke, nicht vereinfacht.")

    verts = np.asarray(mesh.vertices, dtype=float) @ _rot_matrix(*MODEL_ROTATION).T
    verts -= (verts.min(0) + verts.max(0)) / 2
    extent = max(np.ptp(verts[:, 0]), np.ptp(verts[:, 1]))
    verts *= 2 * GRID_RADIUS / extent
    return verts, np.asarray(mesh.faces)


# =============================================================================
# 3D-Szene  –  vedo offscreen + Screenshot in tk.Canvas
# =============================================================================
class Scene3D:
    def __init__(self, tk_frame, model):
        self._verts, self._faces = model
        offset = BEAM_POINT_OFFSET_MM * 2 * GRID_RADIUS / GRID_DIAMETER_MM
        self._verts = self._verts + np.array([0.0, 0.0, -offset])

        vedo.settings.immediate_rendering = False
        self.plt = Plotter(offscreen=True,
                           size=(RENDER_W, RENDER_H),
                           bg=PLOT_BG, bg2="white")
        self.plt.renderer.SetBackground(
            PLOT_BG[0]/255, PLOT_BG[1]/255, PLOT_BG[2]/255)
        self.plt.renderer.GradientBackgroundOff()

        self._elev =  20.0
        self._azim = -60.0
        self._dist =   7.0
        self._apply_camera()

        self._w2i = vtk.vtkWindowToImageFilter()
        self._w2i.SetInput(self.plt.window)

        self._canvas = tk.Canvas(tk_frame, width=RENDER_W, height=RENDER_H,
                                 bg="#%02x%02x%02x" % PLOT_BG,
                                 highlightthickness=0, cursor="fleur")
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._photo = None

        self._drag_x = 0
        self._drag_y = 0
        self._canvas.bind("<ButtonPress-1>", self._mouse_press)
        self._canvas.bind("<B1-Motion>",     self._mouse_drag)
        self._canvas.bind("<ButtonPress-3>", self._mouse_press)
        self._canvas.bind("<B3-Motion>",     self._mouse_zoom)
        self._canvas.bind("<MouseWheel>",    self._mouse_wheel)
        self._canvas.bind("<Button-4>",      self._mouse_wheel)
        self._canvas.bind("<Button-5>",      self._mouse_wheel)

    # ---------------------------------------------------------------- Kamera
    def _apply_camera(self):
        el  = np.radians(self._elev)
        az  = np.radians(self._azim)
        x   = self._dist * np.cos(el) * np.cos(az)
        y   = self._dist * np.cos(el) * np.sin(az)
        z   = self._dist * np.sin(el)
        cam = self.plt.renderer.GetActiveCamera()
        cam.SetPosition(x, y, z)
        cam.SetFocalPoint(0, 0, 0)
        if abs(self._elev) > 85:
            cam.SetViewUp(np.cos(np.radians(self._azim)),
                          np.sin(np.radians(self._azim)), 0)
        else:
            cam.SetViewUp(0, 0, 1)
        cam.SetViewAngle(25)

    def set_view(self, name):
        self._elev, self._azim = VIEWS[name]
        self._apply_camera()
        self._render()

    # ---------------------------------------------------------------- Maus
    def _mouse_press(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _mouse_drag(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        self._drag_x = event.x
        self._drag_y = event.y
        self._azim -= dx * 0.5
        self._elev  = np.clip(self._elev + dy * 0.5, -89, 89)
        self._apply_camera()
        self._render()

    def _mouse_zoom(self, event):
        dy = event.y - self._drag_y
        self._drag_y = event.y
        self._dist = max(2.0, self._dist + dy * 0.02)
        self._apply_camera()
        self._render()

    def _mouse_wheel(self, event):
        if hasattr(event, 'delta') and event.delta:
            factor = 0.9 if event.delta > 0 else 1.1
        else:
            factor = 0.9 if event.num == 4 else 1.1
        self._dist = max(2.0, self._dist * factor)
        self._apply_camera()
        self._render()

    # ---------------------------------------------------------------- Render
    def _render(self):
        self.plt.window.Render()
        self._w2i.Modified()
        self._w2i.Update()
        img_data = self._w2i.GetOutput()
        w, h, _  = img_data.GetDimensions()
        arr = vtk_to_numpy(img_data.GetPointData().GetScalars())
        arr = arr.reshape(h, w, 3)[::-1]
        self._photo = ImageTk.PhotoImage(Image.fromarray(arr, 'RGB'))
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo)

    # ---------------------------------------------------------------- Szene
    def update(self, stage, angles):
        self.plt.renderer.RemoveAllViewProps()
        cam = self.plt.renderer.GetActiveCamera()

        s     = np.radians(stage)
        rot_y = np.array([[np.cos(s), 0, np.sin(s)],
                          [0,         1, 0         ],
                          [-np.sin(s),0, np.cos(s) ]])

        # --- Autogrid ---
        verts_rot = (self._verts @ rot_y.T).astype(np.float32)
        grid_mesh = Mesh([verts_rot, self._faces])
        grid_mesh.color(MODEL_COLOR).lighting("glossy")
        self.plt.renderer.AddActor(grid_mesh.actor)

        # --- Kippachse ---
        for sign in (-1, 1):
            cyl = Cylinder(pos=[(0, sign*1.12, 0), (0, sign*1.55, 0)],
                           r=0.014, c=COLORS["stage"])
            self.plt.renderer.AddActor(cyl.actor)

        # --- Beam-Pfeile ---
        # Alle Spitzen treffen sich nahe am gemeinsamen Punkt (BEAM_TIP_OFFSET
        # entlang der jeweiligen Beam-Achse vom Ursprung entfernt)
        for key, phi_deg in BEAMS.items():
            phi   = np.radians(phi_deg)
            axis  = np.array([np.sin(phi), 0.0, np.cos(phi)])
            col   = COLORS[key]
            rgb   = _hex_to_rgb(col)

            # Pfeilspitze leicht versetzt vom Ursprung (Strahlen treffen sich nahe zusammen)
            tip       = axis * BEAM_TIP_OFFSET
            head_base = axis * (HEAD_LENGTH + BEAM_TIP_OFFSET)
            p_base    = axis * BEAM_LENGTH

            # Schaft
            shaft = Cylinder(pos=[p_base, head_base], r=SHAFT_RADIUS, c=col)
            self.plt.renderer.AddActor(shaft.actor)

            # Pfeilspitze
            head = Cone(pos=head_base, r=HEAD_RADIUS,
                        height=HEAD_LENGTH, axis=-axis, c=col)
            self.plt.renderer.AddActor(head.actor)

            # Billboard-Label: Zeile 1 = Beam-Name, Zeile 2 = Winkel
            lpos    = axis * BEAM_LENGTH * LABEL_FACTOR
            angle_str = f"{angles[key]+0.0:.1f}\u00b0"
            followers = make_follower_label(
                LABELS[key], angle_str, lpos, rgb, LABEL_SCALE, cam)
            for f in followers:
                self.plt.renderer.AddActor(f)

        self._render()


# =============================================================================
# GUI
# =============================================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Arctis Angle Calculation")
        root.geometry("1060x720")
        root.minsize(920, 640)
        root.configure(bg=UI_BG)

        self.vars    = {k: tk.StringVar() for k in LABELS}
        self.entries = {}
        self.status  = tk.StringVar(value="Type an angle and press Enter, or drag the slider.")
        self.stage   = None
        self._busy   = False

        self._setup_style()
        self._build_controls()
        self._build_plot()

        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        self.set_stage(0.0)

    # ---------------------------------------------------------------- Style
    def _setup_style(self):
        base = tkfont.nametofont("TkDefaultFont")
        base.configure(size=10)
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("TFrame",        background=UI_BG)
        s.configure("Card.TFrame",   background=CARD_BG)
        s.configure("TLabel",        background=UI_BG)
        s.configure("Card.TLabel",   background=CARD_BG)
        s.configure("Title.TLabel",  font=(base.actual("family"), 16, "bold"),
                    foreground="#111827")
        s.configure("Sub.TLabel",    foreground="#6b7280")
        s.configure("CardTitle.TLabel", background=CARD_BG, foreground="#6b7280",
                    font=(base.actual("family"), 8, "bold"))
        s.configure("Hint.TLabel",   background=CARD_BG, foreground="#9ca3af",
                    font=(base.actual("family"), 8))
        s.configure("Status.TLabel",    foreground="#6b7280")
        s.configure("StatusErr.TLabel", foreground="#b00020")
        s.configure("Value.TEntry",  fieldbackground="#ffffff", padding=4)
        s.configure("Err.TEntry",    fieldbackground="#ffe3e3",
                    foreground="#b00020", padding=4)
        s.configure("Preset.TButton", padding=(8, 6),
                    background="#f3f4f6", borderwidth=1)
        s.map("Preset.TButton", background=[("active", "#e0e7ff")])
        s.configure("Card.Horizontal.TScale", background=CARD_BG)

    # ------------------------------------------------------------- Controls
    def _card(self, parent, title, row):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 10))
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.columnconfigure(1, weight=1)
        ttk.Label(card, text=title, style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))
        return card

    def _build_controls(self):
        left = ttk.Frame(self.root, padding=(16, 14))
        left.grid(row=0, column=0, sticky="ns")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(5, weight=1)

        ttk.Label(left, text="Arctis Angle Calculator",
                  style="Title.TLabel").grid(row=0, sticky="w")
        ttk.Label(left, text="Enter any angle - all others update automatically.",
                  style="Sub.TLabel").grid(row=1, sticky="w", pady=(0, 12))

        # --- Winkel
        card = self._card(left, "ANGLES  (degrees)", 2)
        for i, key in enumerate(LABELS, start=1):
            ttk.Label(card, text="●", foreground=COLORS[key],
                      style="Card.TLabel").grid(row=i, column=0, padx=(0, 6), pady=3)
            ttk.Label(card, text=LABELS[key], style="Card.TLabel",
                      width=14).grid(row=i, column=1, sticky="w")
            e = ttk.Entry(card, textvariable=self.vars[key], width=8,
                          justify="right", style="Value.TEntry")
            e.grid(row=i, column=2, padx=(4, 8))
            lo, hi = FIELD_RANGE[key]
            ttk.Label(card, text=f"{lo:g} … {hi:g}",
                      style="Hint.TLabel").grid(row=i, column=3, sticky="e")
            e.bind("<Return>",   lambda ev, k=key: self.apply(k))
            e.bind("<KP_Enter>", lambda ev, k=key: self.apply(k))
            e.bind("<FocusOut>", lambda ev, k=key: self.apply(k, silent=True))
            e.bind("<FocusIn>",
                   lambda ev, w=e: w.after(10, lambda: w.selection_range(0, tk.END)))
            e.bind("<Up>",   lambda ev, k=key: self.apply(k, step=+1))
            e.bind("<Down>", lambda ev, k=key: self.apply(k, step=-1))
            self.entries[key] = e

        self.scale = ttk.Scale(card, from_=STAGE_RANGE[0], to=STAGE_RANGE[1],
                               orient="horizontal", command=self._on_slider,
                               style="Card.Horizontal.TScale")
        self.scale.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        ttk.Label(card, text="Drag to tilt the stage  ·  ↑ / ↓ in a field: ±1°",
                  style="Hint.TLabel").grid(row=7, column=0, columnspan=4, sticky="w")

        # --- Presets
        card = self._card(left, "PRESETS", 3)
        for i, (name, angle) in enumerate(PRESETS, start=1):
            ttk.Button(card, text=f"{name}   ({angle}°)", style="Preset.TButton",
                       command=lambda a=angle: self.set_stage(a)).grid(
                row=i, column=0, columnspan=4, sticky="ew", pady=2)

        # --- Ansicht
        card = self._card(left, "VIEW", 4)
        for i, name in enumerate(VIEWS):
            ttk.Button(card, text=name, style="Preset.TButton",
                       command=lambda n=name: self.scene.set_view(n)).grid(
                row=1, column=i, sticky="ew", padx=2)
            card.columnconfigure(i, weight=1)
        ttk.Label(card,
                  text="Left-drag: rotate  ·  Scroll/Right-drag: zoom\n"
                       "Grey stubs = tilt axis of the stage",
                  style="Hint.TLabel").grid(row=2, column=0, columnspan=4,
                                            sticky="w", pady=(6, 0))

        # --- Status + Footer
        self.status_label = ttk.Label(left, textvariable=self.status,
                                      style="Status.TLabel", wraplength=330)
        self.status_label.grid(row=5, sticky="nw")

        footer = ttk.Frame(left)
        footer.grid(row=6, sticky="sw")
        try:
            logo = Image.open("cssb_logo.png").resize((100, 34), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(logo)
            ttk.Label(footer, image=self._logo).grid(row=0, column=0, padx=(0, 10))
        except Exception:
            pass
        ttk.Label(footer, text="Created by Tim Laugks · July 2025", style="Sub.TLabel",
                  font=(tkfont.nametofont("TkDefaultFont").actual("family"), 8)).grid(
            row=0, column=1)

    # ----------------------------------------------------------------- Plot
    def _build_plot(self):
        frame = ttk.Frame(self.root, padding=(0, 14, 16, 14))
        frame.grid(row=0, column=1, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.scene = Scene3D(frame, load_model())

    # ------------------------------------------------------------- Aktionen
    def _on_slider(self, value):
        if self._busy:
            return
        self.set_stage(round(float(value), 1))

    def _clear_errors(self):
        for e in self.entries.values():
            e.configure(style="Value.TEntry")
        self.status_label.configure(style="Status.TLabel")

    def _error(self, key, msg):
        self.entries[key].configure(style="Err.TEntry")
        self.status_label.configure(style="StatusErr.TLabel")
        self.status.set(msg)

    def apply(self, key, step=0, silent=False):
        txt = self.vars[key].get().strip().replace(",", ".")
        try:
            val = float(txt) + step
        except ValueError:
            if silent:
                self._refresh_fields()
            else:
                self._error(key, f"{LABELS[key]}: please enter a number.")
            return
        stage = STAGE_FROM[key](val)
        if not (STAGE_RANGE[0] - 1e-9 <= stage <= STAGE_RANGE[1] + 1e-9):
            lo, hi = FIELD_RANGE[key]
            if silent:
                self._refresh_fields()
            else:
                self._error(key, f"{LABELS[key]}: value must be between {lo:g} and {hi:g}.")
            return
        if self.stage is not None and abs(stage - self.stage) < 1e-9:
            self._refresh_fields()
            return
        self.set_stage(stage)

    def _refresh_fields(self):
        for key, v in angles_from_stage(self.stage).items():
            self.vars[key].set(f"{v + 0.0:.2f}")
        self._clear_errors()

    def set_stage(self, stage):
        self.stage = float(stage)
        self._refresh_fields()
        self._busy = True
        self.scale.set(self.stage)
        self._busy = False
        self.status.set("Type an angle and press Enter, or drag the slider.")
        self.scene.update(self.stage, angles_from_stage(self.stage))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
