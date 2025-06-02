import os

def runarg(app, args):
    if not args or len(args) < 1:
        app.print_text("Usage: /open <.txt_path>\n", 'info')
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = args[0]
    input_dir = os.path.join(script_dir, input_file)

    if not input_file.lower().endswith(".txt"):
        error_msg = "Input file must have a .txt extension"
        app.print_text(error_msg + "\n", 'error')
    else:
        with open(input_dir, "r", encoding="utf-8") as f:
            text = f.read()
            app.print_text(str(text) + '\n')
