import subprocess, os, shutil

def runarg(app, args):
    if not args or len(args) < 1:
        app.print_text("Usage: /video_player <video_name.mp4/.avi/...>\n", 'info')
        return
    
    if shutil.which("ffplay") is None:
        app.print_text("ffplay not found. Make sure FFmpeg is installed and ffplay is in your PATH.\n", 'error')
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
    except subprocess.CalledProcessError as e:
        app.print_text("Error running ffplay: {e}\n", 'error')
    except FileNotFoundError:
        app.print_text("ffplay not found. Make sure FFmpeg is installed and ffplay is in your PATH.\n", 'error')
