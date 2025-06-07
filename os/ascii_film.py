import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyopencl as cl
import time
import os
import subprocess
import concurrent.futures
import queue

ASCII_CHARS = "@#%"
NUM_CHARS = len(ASCII_CHARS)

def setup_opencl():
    platforms = cl.get_platforms()
    devices = []
    for p in platforms:
        for d in p.get_devices(device_type=cl.device_type.GPU):
            devices.append(d)
            print(f"Found GPU device: {d.name} (Vendor: {d.vendor})")

    if len(devices) == 0:
        raise RuntimeError("No GPU devices found.")
    device = devices[1]
    print(f"Using GPU device: {device.name} (Vendor: {device.vendor})")

    ctx = cl.Context([device])
    queue = cl.CommandQueue(ctx)

    kernel_code = """
    __kernel void render_ascii_color_batch(
        __global const uchar *src_bgr,   
        __global const uchar *glyphs,    
        __global uchar *dst_bgr,         
        const int cols,
        const int rows,
        const int char_width,
        const int char_height,
        const int num_chars,
        const int batch_size)
    {
        int out_x = get_global_id(0);
        int out_y = get_global_id(1);
        int batch_idx = get_global_id(2);

        if (batch_idx >= batch_size) return;

        int out_width = cols * char_width;
        int out_height = rows * char_height;

        if (out_x >= out_width || out_y >= out_height) return;

        int cell_x = out_x / char_width;
        int cell_y = out_y / char_height;
        if (cell_x >= cols || cell_y >= rows) return;

        int src_idx = ((batch_idx * rows * cols) + (cell_y * cols + cell_x)) * 3;
        uchar b = src_bgr[src_idx + 0];
        uchar g = src_bgr[src_idx + 1];
        uchar r = src_bgr[src_idx + 2];

        int brightness = (r + g + b) / 3;
        int char_idx = (brightness * (num_chars - 1)) / 255;

        int glyph_idx = ((char_idx * char_height + (out_y % char_height))
                         * char_width) + (out_x % char_width);
        uchar mask = glyphs[glyph_idx];

        int dst_idx = ((batch_idx * out_height * out_width) + (out_y * out_width + out_x)) * 3;
        dst_bgr[dst_idx + 0] = (uchar)((mask * b) / 255);
        dst_bgr[dst_idx + 1] = (uchar)((mask * g) / 255);
        dst_bgr[dst_idx + 2] = (uchar)((mask * r) / 255);
    }
    """

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

def video_to_ascii_color(app, input_path, output_path,
                         char_width=8, char_height=12, batch_size=200, num_workers=4):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        app.print_text(f"Cannot open video '{input_path}'", 'error')
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    ret, frame = cap.read()
    if not ret:
        app.print_text("Cannot read first frame.", 'error')
        return

    ctx, queue_cl, prg = setup_opencl()
    mf = cl.mem_flags

    height, width, _ = frame.shape
    cols = width // char_width
    rows = height // char_height
    out_width = cols * char_width
    out_height = rows * char_height

    try:
        font = ImageFont.truetype("cour.ttf", size=char_height)
    except:
        font = ImageFont.load_default()
    glyphs_flat = pre_render_glyphs(char_width, char_height, font)
    glyphs_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=glyphs_flat)

    src_buf = cl.Buffer(ctx, mf.READ_ONLY, size=batch_size * rows * cols * 3)
    dst_buf = cl.Buffer(ctx, mf.WRITE_ONLY, size=batch_size * out_height * out_width * 3)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height), True)
    if not out.isOpened():
        app.print_text("Failed to initialize VideoWriter.", 'error')
        return

    local_size = (32, 8, 1)
    global_size_template = (
        ((out_width + local_size[0] - 1) // local_size[0]) * local_size[0],
        ((out_height + local_size[1] - 1) // local_size[1]) * local_size[1],
    )

    start_time = time.time()
    frame_count = 0
    frames_queue = queue.Queue(maxsize=batch_size * 2)

    def reader_worker():
        nonlocal ret, frame
        while ret:
            frames_queue.put(frame)
            ret, frame = cap.read()
        for _ in range(num_workers):
            frames_queue.put(None)

    reader_thread = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    reader_thread.submit(reader_worker)

    while True:
        frames_batch = []
        while len(frames_batch) < batch_size:
            f = frames_queue.get()
            if f is None:
                break
            resized = cv2.resize(f, (cols, rows), interpolation=cv2.INTER_NEAREST)
            frames_batch.append(resized)
        if not frames_batch:
            break

        actual_batch_size = len(frames_batch)
        global_size = (*global_size_template, actual_batch_size)
        src_np = np.array(frames_batch, dtype=np.uint8)
        cl.enqueue_copy(queue_cl, src_buf, src_np)

        prg.render_ascii_color_batch(
            queue_cl,
            global_size, local_size,
            src_buf,
            glyphs_buf,
            dst_buf,
            np.int32(cols),
            np.int32(rows),
            np.int32(char_width),
            np.int32(char_height),
            np.int32(NUM_CHARS),
            np.int32(actual_batch_size)
        ).wait()

        dst_np = np.empty((actual_batch_size, out_height, out_width, 3), dtype=np.uint8)
        cl.enqueue_copy(queue_cl, dst_np, dst_buf)

        for i in range(actual_batch_size):
            out.write(dst_np[i])
            frame_count += 1

    cap.release()
    out.release()

    elapsed = time.time() - start_time
    app.print_text(f"Processing complete!\n"
                   f"Total frames processed: {frame_count}\n", 'info')
    app.print_text(f"Elapsed time: {elapsed:.3f} seconds\n", 'info')
    app.print_text(f"Average per-frame: {elapsed/frame_count:.5f} seconds\n", 'info')

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
        subprocess.run(cmd, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.replace(temp_output, output_video)
        app.print_text("Audio merged successfully!\n", 'info')
    except subprocess.CalledProcessError as e:
        app.print_text("Error merging audio:\n", 'error')
        app.print_text(e.stderr.decode(), 'error')

def runarg(app=None, args=None):
    if not args or len(args) < 2:
        app.print_text("Usage: /ascii_film <input_video_path> "
                       "<output_video_path>", 'info')
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, str(args[0]))
    output_path = os.path.join(script_dir, str(args[1]))
    video_to_ascii_color(app, input_path, output_path)