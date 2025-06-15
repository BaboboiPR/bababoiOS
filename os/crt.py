import cv2
import numpy as np
import taichi as ti
import time
import os
from queue import Queue
import threading

# Taichi init: OpenGL backend, disable debug for speed
ti.init(arch=ti.opengl, debug=False)
os.environ["TI_DEBUG"] = "0"

ASCII_CHARS = "█"  # your single glyph
CACHE_DEPTH = 3
char_width, char_height = 2, 3

# Persistent buffers (initialized later)
brightness_map = None
out_img = None

# We'll keep last CACHE_DEPTH grayscale numpy arrays for caching and fast diff
gray_cache_np = []

@ti.kernel
def compute_brightness(frame: ti.types.ndarray(dtype=ti.i32),
                       brightness_map: ti.types.ndarray(dtype=ti.i32),
                       cols: ti.i32, rows: ti.i32):
    for y, x in ti.ndrange(rows, cols):
        r = frame[y, x, 0]
        g = frame[y, x, 1]
        b = frame[y, x, 2]
        brightness_map[y, x] = (r + g + b) // 3

@ti.kernel
def render_ascii_single_glyph(brightness_map: ti.types.ndarray(dtype=ti.i32),
                              out_img: ti.types.ndarray(dtype=ti.i32),
                              char_width: ti.i32, char_height: ti.i32,
                              color_frame: ti.types.ndarray(dtype=ti.i32),
                              cols: ti.i32, rows: ti.i32):
    for y, x in ti.ndrange(rows, cols):
        r = color_frame[y, x, 0]
        g = color_frame[y, x, 1]
        b = color_frame[y, x, 2]
        for dy, dx in ti.ndrange(char_height, char_width):
            out_y = y * char_height + dy
            out_x = x * char_width + dx
            out_img[out_y, out_x, 0] = r
            out_img[out_y, out_x, 1] = g
            out_img[out_y, out_x, 2] = b

def frame_to_ascii_single(frame, cols, rows, frame_index):
    global brightness_map, out_img, gray_cache_np

    # Resize frame to smaller grid
    small_np = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_NEAREST).astype(np.int32)

    # Compute grayscale for cache check
    current_gray = small_np.mean(axis=2).astype(np.int32)

    # Cache hit check — if frame similar to any cached grayscale, skip re-render
    for cached_gray in gray_cache_np:
        diff = np.abs(current_gray - cached_gray).mean()
        if diff < 2.0:
            # Return None to indicate no update needed
            return None

    # Update cache with current grayscale frame (rotate cache)
    if len(gray_cache_np) < CACHE_DEPTH:
        gray_cache_np.append(current_gray)
    else:
        gray_cache_np[frame_index % CACHE_DEPTH] = current_gray

    # Upload resized frame to Taichi ndarray
    small_ti = ti.ndarray(dtype=ti.i32, shape=small_np.shape)
    small_ti.from_numpy(small_np)

    # Compute brightness and render ASCII block glyph
    compute_brightness(small_ti, brightness_map, cols, rows)
    render_ascii_single_glyph(brightness_map, out_img, char_width, char_height, small_ti, cols, rows)

    # Return rendered image as uint8 numpy array
    return np.clip(out_img.to_numpy(), 0, 255).astype(np.uint8)

def video_to_ascii_gpu_threaded(app, input_path, output_path):
    global brightness_map, out_img

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    ret, frame = cap.read()
    if not ret:
        raise Exception("Cannot read first frame")

    height, width, _ = frame.shape
    cols = width // char_width
    rows = height // char_height

    out_width = cols * char_width
    out_height = rows * char_height

    # Initialize persistent Taichi buffers once
    brightness_map = ti.ndarray(dtype=ti.i32, shape=(rows, cols))
    out_img = ti.ndarray(dtype=ti.i32, shape=(out_height, out_width, 3))

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height), True)
    if not out.isOpened():
        raise Exception("VideoWriter failed to open.")

    frame_queue = Queue(maxsize=16)

    def encoder():
        while True:
            item = frame_queue.get()
            if item is None:
                break
            out.write(item)

    enc_thread = threading.Thread(target=encoder)
    enc_thread.start()

    frame_count = 0
    start_time = time.time()
    prev_ascii = None

    while ret:
        ascii_frame = frame_to_ascii_single(frame, cols, rows, frame_count)

        if ascii_frame is not None:
            frame_queue.put(cv2.cvtColor(ascii_frame, cv2.COLOR_RGB2BGR))
            prev_ascii = ascii_frame
        else:
            # Use previous frame if unchanged
            if prev_ascii is not None:
                frame_queue.put(cv2.cvtColor(prev_ascii, cv2.COLOR_RGB2BGR))

        ret, frame = cap.read()
        frame_count += 1

    cap.release()
    frame_queue.put(None)
    enc_thread.join()
    out.release()

    elapsed = time.time() - start_time
    app.print_text(f"Processed {frame_count} frames in {elapsed:.2f}s, avg {elapsed/frame_count:.3f}s/frame\n")

def runarg(app, args=None):
    if not args or len(args) < 2:
        app.print_text("Usage: /crt <input_video_path> <output_video_path>\n", 'info')
        return

    input_path = args[0]
    output_path = args[1]

    app.print_text(f"Converting video '{input_path}' to ASCII and saving as '{output_path}'...\n", 'info')

    try:
        video_to_ascii_gpu_threaded(app, input_path, output_path)
        app.print_text("Conversion completed successfully!\n", 'info')
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        app.print_text(f"Error: {e}\nTraceback:\n{tb}", 'error')