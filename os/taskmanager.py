import tkinter as tk
from tkinter import messagebox
import psutil

class TaskManager(tk.Toplevel):
    def __init__(self, master, colors):
        super().__init__(master)
        self.title("Task Manager")
        self.geometry("600x400")
        self.colors = colors

        self.configure(bg=self.colors['background'])

        self.proc_listbox = tk.Listbox(self, selectmode=tk.SINGLE, font=self.colors['font'],
                                       bg=self.colors['background'], fg=self.colors['text_default'],
                                       highlightbackground=self.colors['background'],
                                       selectbackground=self.colors['text_user_cmd'])
        self.proc_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self, bg=self.colors['background'])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0,10))

        self.kill_btn = tk.Button(btn_frame, text="Kill Selected", command=self.kill_selected,
                                  bg=self.colors['background'], fg=self.colors['text_default'],
                                  activebackground=self.colors['text_user_cmd'], activeforeground=self.colors['background'],
                                  relief='flat')
        self.kill_btn.pack(side=tk.LEFT)

        self.refresh_btn = tk.Button(btn_frame, text="Refresh List", command=self.refresh_processes,
                                     bg=self.colors['background'], fg=self.colors['text_default'],
                                     activebackground=self.colors['text_user_cmd'], activeforeground=self.colors['background'],
                                     relief='flat')
        self.refresh_btn.pack(side=tk.LEFT, padx=(10,0))

        self.status_label = tk.Label(self, text="Select a process and click Kill",
                                     bg=self.colors['background'], fg=self.colors['text_info'],
                                     font=self.colors['font'])
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.processes = []

    def refresh_processes(self):
        self.proc_listbox.delete(0, tk.END)
        self.processes = []

        psutil.cpu_percent(interval=None)  # update CPU usage cache once

        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                cpu = proc.cpu_percent(interval=None)
                mem = proc.info['memory_info'].rss / (1024*1024)
                line = f"PID: {pid:<6} CPU: {cpu:5.1f}% MEM: {mem:7.1f} MB Name: {name}"
                self.proc_listbox.insert(tk.END, line)
                self.processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.status_label.config(text=f"Loaded {len(self.processes)} processes")

    def kill_selected(self):
        sel = self.proc_listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a process to kill.")
            return
        index = sel[0]
        proc = self.processes[index]
        try:
            proc.kill()
            self.status_label.config(text=f"Killed PID {proc.pid} ({proc.name()})")
            self.refresh_processes()
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            messagebox.showerror("Error", f"Failed to kill process: {e}")

# --- Example launcher code with a preset ---

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Launcher")
        self.geometry("300x150")

        # Your preset for colors and fonts
        self.colors = {
            'background': '#282c34',
            'text_default': '#abb2bf',
            'text_user_cmd': '#61afef',
            'text_info': '#5c6370',
            'font': ('Consolas', 10)
        }

        self.configure(bg=self.colors['background'])

        self.open_tm_btn = tk.Button(self, text="Open Task Manager", command=self.open_task_manager,
                                     bg=self.colors['background'], fg=self.colors['text_default'],
                                     activebackground=self.colors['text_user_cmd'], activeforeground=self.colors['background'],
                                     relief='flat')
        self.open_tm_btn.pack(pady=40)

    def open_task_manager(self):
        # Pass the launcher colors preset to TaskManager
        tm = TaskManager(self, self.colors)
        tm.grab_set()  # optional: make the task manager modal

def run():
    launcher = Launcher()
    launcher.mainloop()

