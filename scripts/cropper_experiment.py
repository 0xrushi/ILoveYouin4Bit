from PIL import Image

def crop_image(image_path: str) -> Image.Image:
    """
    Crops the image from (x1, y1) to (x2, y2) and returns the cropped image.
    
    Parameters:
        image_path (str): The path to the input image file.

    Returns:
        Image.Image: The cropped PIL Image object.
    """
    img = Image.open(image_path)
    
    crop_box = (15, 250, 1040, 1550)
    
    cropped_img = img.crop(crop_box)
    
    return cropped_img

cropped = crop_image('output.png')
cropped.show()
# cropped.save('cropped_image.jpg')  # Save the cropped image