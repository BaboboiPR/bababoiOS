from PIL import Image, ImageEnhance
import numpy as np
import os
import sys

NEW_WIDTH = 150
BRIGHTNESS_FACTOR = 1.25
ASCII_CHARS = "@%#*+=-:. "

def runarg(app=None, args=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Require exactly 2 arguments: input image filename and output text filename
    if not args or len(args) < 2:
        error_msg = "Usage: image_to_ascii.py <input_image_name> <output_file_name.txt>\n"
        app.print_text(error_msg, 'error')

    input_filename = args[0]
    output_filename = args[1]

    # Check if output has .txt extension
    if not output_filename.lower().endswith(".txt"):
        error_msg = "Output file must have a .txt extension"
        app.print_text(error_msg + "\n", 'error')

    input_path = os.path.join(script_dir, input_filename)
    output_path = os.path.join(script_dir, output_filename)

    app.print_text(f"Converting image '{input_path}' to ASCII...\n", 'info')

    def resize_image(image, new_width=100):
        width, height = image.size
        aspect_ratio = height / width
        new_height = int(new_width * aspect_ratio * 0.55)
        return image.resize((new_width, new_height))

    def grayscale(image):
        return image.convert("L")

    def pixels_to_ascii(image):
        pixels = np.array(image, dtype=np.uint16)
        ascii_str = ""
        for row in pixels:
            for pixel in row:
                index = pixel * (len(ASCII_CHARS) - 1) // 255
                ascii_str += ASCII_CHARS[index]
            ascii_str += "\n"
        return ascii_str

    def image_to_ascii(path, new_width=100):
        try:
            image = Image.open(path)
        except Exception as e:
            print(f"Could not open image: {e}")
            return None

        image = ImageEnhance.Brightness(image).enhance(BRIGHTNESS_FACTOR)
        image = resize_image(image, new_width)
        gray_image = grayscale(image)
        return pixels_to_ascii(gray_image)

    ascii_output = image_to_ascii(input_path, NEW_WIDTH)

    if ascii_output:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ascii_output)
        print(f"ASCII art saved to: {output_path}")
