import zstandard as zstd
import os

def runarg(app, args):
    if not args:
        app.print_text("Usage: !decompressor <file.zst>\n", 'info')
        return

    input_path = args[0]
    if not os.path.isfile(input_path):
        app.print_text(f"File not found: {input_path}\n", 'error')
        return

    if not input_path.endswith('.zst'):
        app.print_text("Expected a .zst file\n", 'error')
        return

    output_path = input_path[:-4]  # remove .zst

    try:
        dctx = zstd.ZstdDecompressor()
        with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
            dctx.copy_stream(fin, fout)
        app.print_text(f"Decompressed: {output_path}\n", 'info')
    except Exception as e:
        app.print_text(f"Decompression failed: {e}\n", 'error')
