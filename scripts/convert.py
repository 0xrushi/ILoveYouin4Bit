from PIL import Image
import sys

def convert_to_4bit(input_path: str, output_path: str) -> None:
    """
    Converts an image to a 4-bit (16 color) palette and resizes it to fit within 350x350 pixels.

    Args:
        input_path (str): Path to the input image file.
        output_path (str): Path where the converted image will be saved.
    """
    img = Image.open(input_path)
    img.thumbnail((350, 350), Image.LANCZOS)
    img_4bit = img.convert('P', palette=Image.ADAPTIVE, colors=16)
    img_4bit.save(output_path)
    print(f"Saved 4-bit image to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert.py input_image output_image")
        sys.exit(1)
    convert_to_4bit(sys.argv[1], sys.argv[2])