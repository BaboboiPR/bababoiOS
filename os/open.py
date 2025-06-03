import os, threading, pygame

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

def runarg(app, args):
    if not args or len(args) < 1:
        app.print_text("Usage: /open <.txt_path>\n", 'info')
        nuh_uh()
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = args[0]
    input_dir = os.path.join(script_dir, input_file)

    if not input_file.lower().endswith(".txt"):
        error_msg = "Input file must have a .txt extension"
        app.print_text(error_msg + "\n", 'error')
        nuh_uh()
    else:
        with open(input_dir, "r", encoding="utf-8") as f:
            text = f.read()
            app.print_text(str(text) + '\n')
            ding()
