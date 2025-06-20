import subprocess, os, shutil, pygame, threading

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
        app.print_text("Usage: /video_player <video_name.mp4/.avi/...>\n", 'info')
        nuh_uh()
        return

    if shutil.which("ffplay") is None:
        app.print_text("ffplay.exe not found. Make sure FFmpeg is installed and ffplay.exe is in your PATH.\n", 'error')
        nuh_uh()
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, str(args[0]))

    command = [
        "ffplay",
        "-autoexit",
        "-loglevel", "quiet",
        video_path
    ]

    try:
        subprocess.run(command, check=True)
        ding()
    except subprocess.CalledProcessError as e:
        app.print_text("Error running ffplay.exe: {e}\n", 'error')
        nuh_uh()
    except FileNotFoundError:
        app.print_text("ffplay.exe not found. Make sure FFmpeg is installed and ffplay.exe is in your PATH.\n", 'error')
        nuh_uh()
