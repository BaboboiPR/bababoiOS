import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyopencl as cl
import time
import os
import subprocess

ASCII_CHARS = "@#%"
NUM_CHARS = len(ASCII_CHARS)

def setup_opencl():
    platforms = cl.get_platforms()
    devices = [d for p in platforms for d in p.get_devices() if d.type == cl.device_type.GPU]
    device = devices[1] if len(devices) > 1 else devices[0]
    print(f"Using device: {device.name}")
    ctx = cl.Context([device])
    queue = cl.CommandQueue(ctx)

    kernel_code = """
    __kernel void render_ascii_color(
        __global const uchar *src_rgb,
        __global const uchar *glyphs,
        __global uchar *dst_rgb,
        const int src_cols,
        const int src_rows,
        const int char_width,
        const int char_height,
        const int num_chars)
    {
        int out_x = get_global_id(0);
        int out_y = get_global_id(1);

        int cols = src_cols;
        int rows = src_rows;

        int cell_x = out_x / char_width;
        int cell_y = out_y / char_height;

        if (cell_x >= cols || cell_y >= rows)
            return;

        int src_idx = (cell_y * cols + cell_x) * 3;
        uchar r = src_rgb[src_idx];
        uchar g = src_rgb[src_idx + 1];
        uchar b = src_rgb[src_idx + 2];

        int brightness = (r + g + b) / 3;
        int char_idx = (brightness * (num_chars - 1)) / 255;

        int glyph_idx = ((char_idx * char_height + (out_y % char_height)) * char_width) + (out_x % char_width);
        uchar glyph_mask = glyphs[glyph_idx];

        int dst_idx = (out_y * cols * char_width + out_x) * 3;
        dst_rgb[dst_idx]     = (glyph_mask * r) / 255;
        dst_rgb[dst_idx + 1] = (glyph_mask * g) / 255;
        dst_rgb[dst_idx + 2] = (glyph_mask * b) / 255;
    }
    """.strip()

    prg = cl.Program(ctx, kernel_code).build()
    return ctx, queue, prg

def pre_render_glyphs(char_width, char_height, font):
    glyphs = []
    for ch in ASCII_CHARS:
        img = Image.new("L", (char_width, char_height), 0)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), ch, font=font, fill=255)
        glyphs.append(np.array(img).astype(np.uint8))
    glyphs_np = np.stack(glyphs)
    return glyphs_np.flatten()

def video_to_ascii_color(app, input_path, output_path, char_width=8, char_height=12):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        app.print_text(f"Cannot open video '{input_path}'", 'error')
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    ret, frame = cap.read()
    if not ret:
        app.print_text("Cannot read first frame.", 'error')
        return

    ctx, queue, prg = setup_opencl()
    mf = cl.mem_flags

    height, width, _ = frame.shape
    cols = width // char_width
    rows = height // char_height
    out_width = cols * char_width
    out_height = rows * char_height

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height), True)
    if not out.isOpened():
        app.print_text("Failed to initialize VideoWriter.", 'error')
        return

    try:
        font = ImageFont.truetype("cour.ttf", size=char_height)
    except:
        font = ImageFont.load_default()

    glyphs_flat = pre_render_glyphs(char_width, char_height, font)
    glyphs_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=glyphs_flat)

    # Preallocate OpenCL buffers
    src_buf = cl.Buffer(ctx, mf.READ_ONLY, cols * rows * 3)
    dst_buf = cl.Buffer(ctx, mf.WRITE_ONLY, out_height * out_width * 3)

    # Double buffers on CPU side
    cpu_buffers = [
        (np.zeros((rows, cols, 3), dtype=np.uint8), np.zeros((out_height, out_width, 3), dtype=np.uint8)),
        (np.zeros((rows, cols, 3), dtype=np.uint8), np.zeros((out_height, out_width, 3), dtype=np.uint8))
    ]
    buffer_index = 0

    start_time = time.time()
    frame_count = 0

    local_size = (16, 16)
    global_size = (
        ((out_width + local_size[0] - 1) // local_size[0]) * local_size[0],
        ((out_height + local_size[1] - 1) // local_size[1]) * local_size[1]
    )

    while ret:
        small_np, out_np = cpu_buffers[buffer_index]

        # CPU side preprocessing
        small_frame = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_NEAREST)
        np.copyto(small_np, small_frame)

        src_flat = small_np.flatten()

        # Asynchronous pipeline (warning: clever!)
        event_copy = cl.enqueue_copy(queue, src_buf, src_flat, is_blocking=False)
        event_kernel = prg.render_ascii_color(
            queue, global_size, local_size,
            src_buf, glyphs_buf, dst_buf,
            np.int32(cols), np.int32(rows),
            np.int32(char_width), np.int32(char_height),
            np.int32(NUM_CHARS),
            wait_for=[event_copy]
        )
        event_read = cl.enqueue_copy(queue, out_np, dst_buf, is_blocking=False, wait_for=[event_kernel])

        # CPU pipeline: read next frame while GPU is busy
        ret, next_frame = cap.read()

        # Wait for GPU to finish current frame
        event_read.wait()

        # Write completed frame
        ascii_bgr = cv2.cvtColor(out_np, cv2.COLOR_RGB2BGR)
        out.write(ascii_bgr)

        # Prepare for next loop
        if ret:
            frame = next_frame
        buffer_index = 1 - buffer_index
        frame_count += 1

    cap.release()
    out.release()

    elapsed = time.time() - start_time
    app.print_text(f"Processing complete!\nTotal frames processed: {frame_count}\n", 'info')
    app.print_text(f"Elapsed time: {elapsed:.2f} seconds\n", 'info')
    app.print_text(f"Average time per frame: {elapsed / frame_count:.3f} seconds\n", 'info')

    merge_audio(app, input_path, output_path)

def merge_audio(app, input_video, output_video):
    temp_output = output_video + '.temp.avi'
    cmd = [
        "ffmpeg",
        "-i", output_video,
        "-i", input_video,
        "-c", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        temp_output
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.replace(temp_output, output_video)
        app.print_text("Audio merged successfully!\n", 'info')
    except subprocess.CalledProcessError as e:
        app.print_text("Error merging audio:", 'error')
        app.print_text(e.stderr.decode(), 'error')


def runarg(app=None, args=None):
    if not args or len(args) < 2:
        app.print_text("Usage: /ascii_film <input_video_path> <output_video_path>", 'info')
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, str(args[0]))
    output_path = os.path.join(script_dir, str(args[1]))
    video_to_ascii_color(app, input_path, output_path)
