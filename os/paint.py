import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox

try:
    from config import PRESETS, DEFAULT_PRESET, current_preset
    current_preset = PRESETS[DEFAULT_PRESET]
except ImportError:
    current_preset = {
        'background': '#222',
        'button_bg': '#333',
        'button_fg': 'white',
        'button_hover_bg': '#4a90e2',
        'button_active_bg': '#1c5dbf',
        'entry_font': ('Segoe UI', 28),
        'font': ('Segoe UI', 14),
        'text_default': 'black'
    }

class AnimatedButton(tk.Button):
    def __init__(self, master=None, hover_bg=None, press_bg=None, **kwargs):
        self.hover_bg = hover_bg or '#4a90e2'
        self.press_bg = press_bg or '#1c5dbf'
        self.default_bg = kwargs.get('bg', '#333')
        self.default_fg = kwargs.get('fg', 'white')
        super().__init__(master=master, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_enter(self, _): self.config(bg=self.hover_bg)
    def on_leave(self, _): self.config(bg=self.default_bg)
    def on_press(self, _): self.config(bg=self.press_bg)
    def on_release(self, _): self.config(bg=self.hover_bg)

def run(app, preset=None):
    if app is None:
        raise ValueError("You must pass the main Tk root window as 'app'")

    colors = preset or current_preset

    paint_win = tk.Toplevel(app)
    paint_win.title("Paint")
    paint_win.geometry("1000x700")
    paint_win.configure(bg=colors['background'])
    paint_win.minsize(600, 400)

    brush_color = colors['text_default']
    brush_size = 5
    prev_x = prev_y = None
    erasing = False

    # --- Layout frames ---
    main_frame = tk.Frame(paint_win, bg=colors['background'])
    main_frame.pack(fill='both', expand=True)

    palette_frame = tk.Frame(main_frame, bg=colors['background'], width=80)
    palette_frame.pack(side='left', fill='y', padx=5, pady=5)

    right_frame = tk.Frame(main_frame, bg=colors['background'])
    right_frame.pack(side='left', fill='both', expand=True)

    toolbar = tk.Frame(right_frame, bg=colors['background'], height=50)
    toolbar.pack(side='top', fill='x', padx=10, pady=5)

    # Canvas frame to make canvas expand
    canvas_frame = tk.Frame(right_frame, bg='black')
    canvas_frame.pack(side='top', fill='both', expand=True, padx=10, pady=(0,10))

    canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0, cursor='crosshair')
    canvas.pack(fill='both', expand=True)

    # --- Drawing functions ---
    def start_draw(event):
        nonlocal prev_x, prev_y
        prev_x, prev_y = event.x, event.y

    def draw(event):
        nonlocal prev_x, prev_y, erasing
        if prev_x is not None and prev_y is not None:
            color = 'white' if erasing else brush_color
            canvas.create_line(
                prev_x, prev_y, event.x, event.y,
                fill=color,
                width=brush_size,
                capstyle=tk.ROUND,
                smooth=True,
                splinesteps=36
            )
        prev_x, prev_y = event.x, event.y

    canvas.bind("<Button-1>", start_draw)
    canvas.bind("<B1-Motion>", draw)

    def clear_canvas():
        canvas.delete("all")

    def choose_color():
        nonlocal brush_color, erasing
        erasing = False
        color = colorchooser.askcolor(title="Select Brush Color")[1]
        if color:
            brush_color = color
            update_color_preview()

    def set_brush_size(new_size):
        nonlocal brush_size
        brush_size = int(new_size)
        brush_size_label.config(text=f"Size: {brush_size}")

    def use_eraser():
        nonlocal erasing
        erasing = True
        update_color_preview()

    def update_color_preview():
        color_display.config(bg='white' if erasing else brush_color)

    def save_drawing():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Save canvas content as postscript, then convert using PIL if available
                canvas.postscript(file=file_path + ".ps", colormode='color')
                try:
                    from PIL import Image
                    img = Image.open(file_path + ".ps")
                    img.save(file_path, 'png')
                    import os
                    os.remove(file_path + ".ps")
                    messagebox.showinfo("Saved", f"Image saved as {file_path}")
                except ImportError:
                    messagebox.showwarning("Pillow not found", "Install Pillow to save as PNG.")
            except Exception as e:
                messagebox.showerror("Save error", f"Failed to save image: {e}")

    # --- Toolbar buttons ---
    btn_style = dict(
        bg=colors['button_bg'],
        fg=colors['button_fg'],
        hover_bg=colors['button_hover_bg'],
        press_bg=colors['button_active_bg'],
        font=colors['font'],
        relief='flat',
        bd=0,
        padx=12,
        pady=6,
        cursor='hand2'
    )

    color_btn = AnimatedButton(toolbar, text="Choose Color", command=choose_color, **btn_style)
    color_btn.pack(side='left', padx=5)

    eraser_btn = AnimatedButton(toolbar, text="Eraser", command=use_eraser, **btn_style)
    eraser_btn.pack(side='left', padx=5)

    clear_btn = AnimatedButton(toolbar, text="Clear Canvas", command=clear_canvas, **btn_style)
    clear_btn.pack(side='left', padx=5)

    save_btn = AnimatedButton(toolbar, text="Save", command=save_drawing, **btn_style)
    save_btn.pack(side='left', padx=5)

    # Brush size slider
    size_frame = tk.Frame(toolbar, bg=colors['background'])
    size_frame.pack(side='left', padx=15)

    brush_size_label = tk.Label(size_frame, text=f"Size: {brush_size}", fg=colors['button_fg'], bg=colors['background'], font=colors['font'])
    brush_size_label.pack(anchor='w')

    size_slider = tk.Scale(size_frame, from_=1, to=50, orient='horizontal', bg=colors['background'],
                           fg=colors['button_fg'], troughcolor=colors['button_bg'], highlightthickness=0,
                           command=set_brush_size, length=150)
    size_slider.set(brush_size)
    size_slider.pack()

    # Color preview box
    color_preview_label = tk.Label(toolbar, text="Brush Color:", fg=colors['button_fg'], bg=colors['background'], font=colors['font'])
    color_preview_label.pack(side='left', padx=(20, 5))

    color_display = tk.Label(toolbar, bg=brush_color, width=3, height=1, relief='sunken', bd=2)
    color_display.pack(side='left')

    update_color_preview()

    # --- Color palette ---
    palette_colors = [
        '#000000', '#7f7f7f', '#880015', '#ed1c24', '#ff7f27', '#fff200',
        '#22b14c', '#00a2e8', '#3f48cc', '#a349a4', '#ffffff', '#c3c3c3',
        '#b97a57', '#ffaec9', '#ffc90e', '#efe4b0', '#b5e61d', '#99d9ea',
        '#7092be', '#c8bfe7'
    ]

    def palette_click(color):
        nonlocal brush_color, erasing
        erasing = False
        brush_color = color
        update_color_preview()

    for c in palette_colors:
        btn = tk.Button(palette_frame, bg=c, width=3, height=1, relief='raised', bd=1,
                        command=lambda col=c: palette_click(col), cursor='hand2')
        btn.pack(pady=3, padx=3)

