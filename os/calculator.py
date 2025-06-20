import tkinter as tk
import time

class AnimatedButton(tk.Button):
    def __init__(self, master=None, hover_bg=None, press_bg=None, **kw):
        self.hover_bg = hover_bg or '#4a90e2'
        self.press_bg = press_bg or '#1c5dbf'
        self.default_bg = kw.get('bg', '#333')
        self.default_fg = kw.get('fg', 'white')
        super().__init__(master=master, **kw)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_enter(self, e):
        self.config(bg=self.hover_bg)
    def on_leave(self, e):
        self.config(bg=self.default_bg)
    def on_press(self, e):
        self.config(bg=self.press_bg)
    def on_release(self, e):
        self.config(bg=self.hover_bg)

def run(app, preset=None):
    if app is None:
        raise ValueError("You must pass the main Tk root window as 'app'")

    colors = preset or {
        'background': '#222',
        'button_bg': '#333',
        'button_fg': 'white',
        'button_hover_bg': '#4a90e2',
        'button_active_bg': '#1c5dbf',
        'entry_font': ('Segoe UI', 28),
        'font': ('Segoe UI', 24, 'bold')
    }

    calc = tk.Toplevel(app)
    calc.title("Calculator")
    calc.geometry("350x500")
    calc.configure(bg=colors['background'])
    calc.resizable(False, False)

    expression = ""
    last_operator = False
    press_delay = 0.1
    last_press_time = {}

    operators = set("+-*/")

    def can_press_number(num):
        now = time.time()
        if num in last_press_time:
            diff = now - last_press_time[num]
            if diff < press_delay * (last_press_time.get(f"count_{num}", 1)):
                return False
            last_press_time[f"count_{num}"] = last_press_time.get(f"count_{num}", 1) + 1
        else:
            last_press_time[f"count_{num}"] = 1
        last_press_time[num] = now
        return True

    def press(char):
        nonlocal expression, last_operator
        if char in operators:
            if not expression or last_operator:
                return
            expression += char
            last_operator = True
            for key in list(last_press_time):
                if key.startswith("count_"):
                    last_press_time[key] = 1
        else:
            if not can_press_number(char):
                return
            expression += char
            last_operator = False
        equation.set(expression)

    def equalpress():
        nonlocal expression, last_operator
        try:
            result = eval(expression)
            if isinstance(result, float) and result.is_integer():
                result = int(result)  # Convert 4.0 → 4
            total = str(result)
            equation.set(total)
            expression = total
            last_operator = False
            last_press_time.clear()
        except Exception:
            equation.set("Error")
            expression = ""
            last_operator = False
            last_press_time.clear()

    def clear():
        nonlocal expression, last_operator
        expression = ""
        equation.set("")
        last_operator = False
        last_press_time.clear()

    equation = tk.StringVar()
    expression_field = tk.Entry(
        calc,
        textvariable=equation,
        font=colors['entry_font'],
        bd=0,
        relief='flat',
        justify='right',
        state='readonly',
        readonlybackground=colors['background'],
        fg=colors['button_fg'],
        insertbackground=colors['button_fg']
    )
    expression_field.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=20, pady=(20, 10), ipady=20)

    buttons = [
        ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
        ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
        ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
        ('0', 4, 0), ('.', 4, 1), ('C', 4, 2), ('+', 4, 3),
        ('=', 5, 0, 4)
    ]

    for (text, row, col, colspan) in [(*btn, 1) if len(btn) == 3 else btn for btn in buttons]:
        def cmd(x=text):
            if x == '=':
                equalpress()
            elif x == 'C':
                clear()
            else:
                press(x)
        btn = AnimatedButton(
            calc,
            text=text,
            command=cmd,
            font=colors['font'],
            bg=colors['button_bg'],
            fg=colors['button_fg'],
            hover_bg=colors['button_hover_bg'],
            press_bg=colors['button_active_bg'],
            activeforeground=colors['button_fg'],
            activebackground=colors['button_active_bg'],
            relief='flat',
            cursor='hand2',
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=10
        )
        btn.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=12, pady=12)

    for i in range(6):
        calc.grid_rowconfigure(i, weight=1)
    for i in range(4):
        calc.grid_columnconfigure(i, weight=1)
