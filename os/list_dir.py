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

def run(app):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(script_dir)

    try:
        for file in files:
            if file.find(".") != -1:
                app.print_text(file + "\n")
                ding()
            else:
                app.print_text("FOLDER: " + file + "\n")
    except Exception as e:
        app.print_text("Error executing command: " + {e} + "\n", 'error')
        nuh_uh()