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
    if len(args) != 2:
        app.print_text('Usage: /rename \"<"original filename">\" \"<"new filename">\"\n', 'info')
        nuh_uh()
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))

    input_name = args[0].strip('"').strip("'")
    output_name = args[1].strip('"').strip("'")

    input_file = os.path.join(script_dir, input_name)
    output_file = os.path.join(script_dir, output_name)

    try:
        if not os.path.exists(input_file):
            app.print_text(f"File not found: {input_name}\n", 'error')
            nuh_uh()
            return

        os.replace(input_file, output_file)
        app.print_text(f"Successfully renamed '{input_name}' to '{output_name}'!\n", 'info')
        ding()
    except Exception as e:
        app.print_text(f"Error executing command: {e}\n", 'error')
        nuh_uh()