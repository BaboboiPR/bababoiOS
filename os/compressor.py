import zstandard as zstd
import os

def runarg(app, args):
    if not args:
        app.print_text("Usage: /compressor <filepath>\n", 'info')
        return

    input_path = args[0]
    if not os.path.isfile(input_path):
        app.print_text(f"File not found: {input_path}\n", 'error')
        return

    output_path = input_path + '.zst'

    try:
        cctx = zstd.ZstdCompressor(level=10)
        with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
            cctx.copy_stream(fin, fout)
        app.print_text(f"Compressed: {output_path}\n", 'info')
    except Exception as e:
        app.print_text(f"Compression failed: {e}\n", 'error')
