import zstandard as zstd
import os, threading, pygame, time

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
    if not args:
        app.print_text("Usage: /compressor <filepath> <compression_level (1-22 [11 - best for speed and compression])>\n", 'info')
        nuh_uh()
        return
    elif len(args) < 2:
        app.print_text("Usage: /compressor <filepath> <compression_level (1-22 [11 - best for speed and compression])>\n", 'info')
        nuh_uh()
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = args[0]
    input_path1 = os.path.join(script_dir, input_path)

    if not os.path.isfile(input_path1):
        app.print_text(f"File not found: {input_path1}\n", 'error')
        nuh_uh()
        return

    output_path = input_path1 + '.zst'
    level = int(args[1])
    READ_SZ  = 1 << 20

    try:
        cctx = zstd.ZstdCompressor(level=level, threads=-1)
        start = time.time()
        with open(input_path1, 'rb') as fin, open(output_path, 'wb') as fout:
            writer = cctx.stream_writer(fout)
            for chunk in iter(lambda: fin.read(READ_SZ), b''):
                writer.write(chunk)
            writer.flush(zstd.FLUSH_FRAME)
        duration = time.time() - start

        orig = os.path.getsize(input_path1)
        comp = os.path.getsize(output_path)
        ratio = comp / orig

        app.print_text(
            f"Compressed: {output_path}  "
            f"Time: {duration:.2f}s  "
            f"Ratio: {ratio:.2%}\n", 'info'
        )
        ding()
    except Exception as e:
        app.print_text(f"Compression failed: {e}\n", 'error')
        nuh_uh()