import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import taichi as ti
import traceback
import os
import time
from pathlib import Path

# Initialize Taichi
ti.init(arch=ti.opengl)
os.environ["TI_DEBUG"] = "0"

ASCII_CHARS = "@#%"
NUM_CHARS = len(ASCII_CHARS)
CACHE_DEPTH = 3


def pre_render_chars(char_width, char_height, font):
    glyphs = []
    for ch in ASCII_CHARS:
        img = Image.new("RGB", (char_width, char_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), ch, font=font, fill=(255, 255, 255))
        glyphs.append(np.array(img).astype(np.int32))
    return np.array(glyphs)


@ti.kernel
def compute_brightness(frame: ti.types.ndarray(dtype=ti.i32), #type: ignore
                       brightness_map: ti.types.ndarray(dtype=ti.i32), #type: ignore
                       cols: ti.i32, rows: ti.i32): #type: ignore
    for y, x in ti.ndrange(rows, cols):
        r = frame[y, x, 0]
        g = frame[y, x, 1]
        b = frame[y, x, 2]
        brightness = (r + g + b) // 3
        idx = brightness * (ti.static(NUM_CHARS) - 1) // 255
        brightness_map[y, x] = idx


@ti.kernel
def render_ascii_gpu(brightness_map: ti.types.ndarray(dtype=ti.i32), #type: ignore
                     glyphs: ti.types.ndarray(dtype=ti.i32), #type: ignore
                     color_frame: ti.types.ndarray(dtype=ti.i32), #type: ignore
                     out_img: ti.types.ndarray(dtype=ti.i32), #type: ignore
                     char_width: ti.i32, char_height: ti.i32, #type: ignore
                     cols: ti.i32, rows: ti.i32): #type: ignore
    for y, x in ti.ndrange(rows, cols):
        idx = brightness_map[y, x]
        r = color_frame[y, x, 0]
        g = color_frame[y, x, 1]
        b = color_frame[y, x, 2]

        for dy, dx in ti.ndrange(char_height, char_width):
            glyph_val = glyphs[idx, dy, dx, 0]
            val = glyph_val * r // 255, glyph_val * g // 255, glyph_val * b // 255
            out_y = y * char_height + dy
            out_x = x * char_width + dx
            out_img[out_y, out_x, 0] = val[0]
            out_img[out_y, out_x, 1] = val[1]
            out_img[out_y, out_x, 2] = val[2]


def frame_to_ascii_gpu(frame, glyphs_cpu, glyphs_gpu, char_width, char_height,
                       gray_buffer, buffer_index):
    height, width, _ = frame.shape
    cols = width // char_width
    rows = height // char_height

    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    small_img = pil_img.resize((cols, rows), Image.NEAREST)
    small_np = np.array(small_img).astype(np.int32)

    current_gray_gpu = ti.ndarray(dtype=ti.i32, shape=(rows, cols))
    current_gray_gpu.from_numpy(np.mean(small_np, axis=2).astype(np.int32))

    if gray_buffer:
        prev_gray = gray_buffer[(buffer_index - 1) % CACHE_DEPTH]
        diff = np.abs(current_gray_gpu.to_numpy() - prev_gray.to_numpy()).mean()
        if diff < 2.0:  # More tolerant threshold
            return None

    brightness_map = ti.ndarray(dtype=ti.i32, shape=(rows, cols))
    compute_brightness(small_np, brightness_map, cols, rows)

    out_img = ti.ndarray(dtype=ti.i32, shape=(rows * char_height, cols * char_width, 3))
    render_ascii_gpu(brightness_map, glyphs_gpu, small_np, out_img,
                     char_width, char_height, cols, rows)

    if gray_buffer:
        gray_buffer[buffer_index % CACHE_DEPTH].copy_from(current_gray_gpu)

    np_out = out_img.to_numpy()
    return np.clip(np_out, 0, 255).astype(np.uint8)


def fallback_ascii_frame(frame, glyphs_cpu, glyphs_gpu, char_width, char_height):
    # Render without caching or skipping logic
    height, width, _ = frame.shape
    cols = width // char_width
    rows = height // char_height

    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    small_img = pil_img.resize((cols, rows), Image.NEAREST)
    small_np = np.array(small_img).astype(np.int32)

    brightness_map = ti.ndarray(dtype=ti.i32, shape=(rows, cols))
    compute_brightness(small_np, brightness_map, cols, rows)

    out_img = ti.ndarray(dtype=ti.i32, shape=(rows * char_height, cols * char_width, 3))
    render_ascii_gpu(brightness_map, glyphs_gpu, small_np, out_img,
                     char_width, char_height, cols, rows)
    return np.clip(out_img.to_numpy(), 0, 255).astype(np.uint8)


def video_to_ascii_gpu_cached(app, input_path, output_path, char_width=8, char_height=12):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    ret, frame = cap.read()
    if not ret:
        raise Exception("Cannot read first frame")

    try:
        font = ImageFont.truetype("cour.ttf", size=char_height)
    except:
        font = ImageFont.load_default()

    glyphs_cpu = pre_render_chars(char_width, char_height, font)
    glyphs_gpu = ti.ndarray(dtype=ti.i32, shape=glyphs_cpu.shape)
    glyphs_gpu.from_numpy(glyphs_cpu)

    height, width, _ = frame.shape
    out_width = (width // char_width) * char_width
    out_height = (height // char_height) * char_height

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height), True)
    if not out.isOpened():
        raise Exception("VideoWriter failed to open.")

    frame_count = 0
    start_time = time.time()

    cols = width // char_width
    rows = height // char_height
    gray_buffer = [ti.ndarray(dtype=ti.i32, shape=(rows, cols)) for _ in range(CACHE_DEPTH)]
    buffer_index = 0

    prev_ascii_frame = None

    while ret:
        ascii_frame = frame_to_ascii_gpu(frame, glyphs_cpu, glyphs_gpu, char_width,
                                         char_height, gray_buffer, buffer_index)

        if ascii_frame is not None:
            out.write(cv2.cvtColor(ascii_frame, cv2.COLOR_RGB2BGR))
            prev_ascii_frame = ascii_frame
        else:
            if prev_ascii_frame is not None:
                out.write(cv2.cvtColor(prev_ascii_frame, cv2.COLOR_RGB2BGR))
            else:
                ascii_frame = fallback_ascii_frame(frame, glyphs_cpu, glyphs_gpu, char_width, char_height)
                out.write(cv2.cvtColor(ascii_frame, cv2.COLOR_RGB2BGR))
                prev_ascii_frame = ascii_frame

        ret, frame = cap.read()
        frame_count += 1
        buffer_index += 1

    cap.release()
    out.release()

    elapsed = time.time() - start_time
    app.print_text(f"Processed {frame_count} frames in {elapsed:.2f} seconds, average {elapsed / frame_count:.3f} sec/frame\n")

def runarg(app, args=None):
    if not args or len(args) < 2:
        app.print_text("Usage: /ascii_film <input_video_path> <output_video_path>\n", 'info')
        return
    
    input_path = args[0]
    output_path = args[1]

    # Determine the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_path)
    output_path = os.path.join(script_dir, output_path)

    app.print_text(f"Converting video '{input_path}' to ASCII and saving as '{output_path}'...\n", 'info')

    try:
        video_to_ascii_gpu_cached(app, str(input_path), str(output_path))
        app.print_text("Conversion completed successfully!\n", 'info')
    except Exception as e:
        tb = traceback.format_exc()
        app.print_text(f"Error during conversion: {e}\nTraceback:\n{tb}", 'error')
