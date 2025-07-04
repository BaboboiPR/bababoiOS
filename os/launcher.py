# all scripts MUST be in the same directory

import tkinter as tk
import importlib, config, os, sys, platform, psutil, traceback, taskmanager, threading, pygame

pygame.mixer.init()

def ding():
    def _play():
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sounds_dir = os.path.join(script_dir, 'sounds/ding.mp3')
            pygame.mixer.music.load(sounds_dir)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
    threading.Thread(target=_play).start()

def nuh_uh():
    def _play():
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sounds_dir = os.path.join(script_dir, 'sounds/nuh_uh.mp3')
            pygame.mixer.music.load(sounds_dir)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
    threading.Thread(target=_play).start()

def load_commands():
    cmds = {}
    base_dir = os.path.dirname(__file__) if not getattr(sys, 'frozen', False) else os.path.dirname(sys.executable)
    for filename in os.listdir(base_dir):
        if filename.endswith(".py") and filename.lower() not in ("launcher.py", "config.py") and not filename.startswith("_"):
            module_name = filename[:-3]
            cmds[module_name.lower()] = module_name  # store lowercase keys
    return cmds

commands = load_commands()

class MiniCMD(tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_preset_name = config.DEFAULT_PRESET
        self.colors = config.PRESETS[self.current_preset_name]

        self.title("bababoiOS")
        self.configure(bg=self.colors['background'])

        self.output = tk.Text(self, state='disabled', height=20, width=80,
                              bg=self.colors['background'], fg=self.colors['text_default'],
                              insertbackground=self.colors['text_default'],
                              font=self.colors['font'], relief='flat', borderwidth=0, wrap='word')
        self.output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.output.tag_config('user_cmd', foreground=self.colors['text_user_cmd'])
        self.output.tag_config('info', foreground=self.colors['text_info'])
        self.output.tag_config('error', foreground=self.colors['text_error'])
        self.output.tag_config('normal', foreground=self.colors['text_default'])


        self.input_frame = tk.Frame(
            self,
            bg=self.colors.get('outline', self.colors['button_bg']),  # outline color
            padx=1,                                                   # thickness of the outline
            pady=1
        )
        self.input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.input = tk.Entry(
            self.input_frame,
            width=80,
            bg=self.colors['background'],
            fg=self.colors['text_default'],
            insertbackground=self.colors['text_default'],
            font=self.colors['font'],
            relief='flat',
            borderwidth=3 # spacing of the outline
        )
        self.input.pack(fill=tk.X)
        self.input.bind('<Return>', self.process_command)
        self.input.focus()

        self.print_text(
            f"Welcome to bababoiOS! Commands start with '{config.COMMAND_PREFIX}'. "
            f"Type {config.COMMAND_PREFIX}help or {config.COMMAND_PREFIX}exit.\n", 'info'
        )

    def print_text(self, text, tag='normal'):
        self.output.config(state='normal')
        self.output.insert(tk.END, text, tag)
        self.output.see(tk.END)
        self.output.config(state='disabled')

    def clear_output(self):
        self.output.config(state='normal')
        self.output.delete('1.0', tk.END)
        self.output.config(state='disabled')

    def apply_preset(self, preset_name):
        if preset_name not in config.PRESETS:
            self.print_text(f"Preset '{preset_name}' not found.\n", 'error')
            return

        self.current_preset_name = preset_name
        self.colors = config.PRESETS[preset_name]

        self.configure(bg=self.colors['background'])

        self.output.config(
            bg=self.colors['background'],
            fg=self.colors['text_default'],
            insertbackground=self.colors['text_default'],
            font=self.colors['font']
        )
        self.input.config(
            bg=self.colors['background'],
            fg=self.colors['text_default'],
            insertbackground=self.colors['text_default'],
            font=self.colors['font']
        )

        self.input_frame.config(bg=self.colors['button_bg'])
        self.output.tag_config('user_cmd', foreground=self.colors['text_user_cmd'])
        self.output.tag_config('info', foreground=self.colors['text_info'])
        self.output.tag_config('error', foreground=self.colors['text_error'])
        self.output.tag_config('normal', foreground=self.colors['text_default'])

        self.print_text(f"Switched to preset '{preset_name}'.\n", 'info')

    def show_info(self):
        uname = platform.uname()
        information = [
            f"System    : {uname.system}",
            f"Node      : {uname.node}",
            f"Release   : {uname.release}",
            f"Version   : {uname.version}",
            f"Machine   : {uname.machine}",
            f"Processor : {uname.processor}",
            f"RAM       : {round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
            f"Disk      : {round(psutil.disk_usage('/').total / (1024 ** 3), 2)} GB"
        ]

        smiley = [
            "     _______  ",
            "    /       \\ ",
            "   | (•) (•) |",
            "   |    ^    |",
            "   |  \\___/  |",
            "    \\_______/ ",
            ""
        ]

        self.print_text("\n".join(information) + "\n" + "\n".join(smiley))

    def process_command(self, event=None):
        cmd = self.input.get().strip()
        self.print_text(f"> {cmd}\n", 'user_cmd')
        self.input.delete(0, tk.END)

        if not cmd.startswith(config.COMMAND_PREFIX):
            self.print_text(f"Use prefix '{config.COMMAND_PREFIX}'\n", 'error')
            nuh_uh()
            return

        parts = cmd[len(config.COMMAND_PREFIX):].split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        if command == "exit":
            self.print_text("Bye!\n", 'info')
            self.after(1000, self.destroy)
        elif command == "calculator":
            try:
                import calculator
                calculator.run(self, preset=self.colors)
                ding()
            except Exception as e:
                self.print_text(f"Failed to launch calculator: {e}\n", 'error')
                traceback.print_exc()
                nuh_uh()
        elif command == "help":
            cmds_list = list(commands.keys()) + \
                        ["info"] + \
                        [f"preset {preset}" for preset in config.ALL_PRESETS] + \
                        ["help", "exit", "clear"]

            self.print_text("Available commands:\n" + "\n".join(sorted(cmds_list)) + "\n")
            ding()
        elif command == "info":
            self.show_info()
            ding()
        elif command == "preset" and len(args) == 1:
            self.apply_preset(args[0])
            ding()
        elif command == "clear":
            self.clear_output()
            ding()
        elif command == "taskmanager":
            try:
                taskmanager.TaskManager(self, self.colors)
                ding()
            except Exception as e:
                self.print_text(f"Error launching taskmanager: {e}\n", 'error')
                traceback.print_exc()
                nuh_uh()
        elif command in commands:
            self.run_script(command, args)
            # here was supposed to be a ding() function tho if the script errors inside itself the ding will play but the error will appear so idk ill put the sounds inside the scripts and only the necessary ones will be in this launcher.py
        else:
            self.print_text(f"Unknown command: {command}\n", 'error')
            nuh_uh()

    def run_script(self, command, args):
        module_name = commands.get(command.lower())
        if not module_name:
            self.print_text(f"Command '{command}' not found.\n", 'error')
            nuh_uh()
            return

        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'runarg'):
                module.runarg(self, args)
                # again here
            elif hasattr(module, 'run'):
                module.run(self)
                # and again here aswell
            else:
                self.print_text(f"No `run()` or `runarg()` in '{module_name}'.\n", 'error')
                nuh_uh()
        except ImportError as e:
            self.print_text(f"Import error: {e}\n", 'error')
            nuh_uh()
        except Exception as e:
            self.print_text(f"Error running command '{module_name}': {e}\n", 'error')
            traceback.print_exc()
            nuh_uh()

if __name__ == "__main__":
    try:
        app = MiniCMD()
        app.mainloop()
    except Exception as e:
        print("Unhandled exception:", e)
        traceback.print_exc()
        nuh_uh()
    input("Press Enter to exit...")
