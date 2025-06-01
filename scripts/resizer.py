from PIL import Image

# Open the image
image = Image.open('output_resized2.png')

# Resize the image to 128x128 pixels using LANCZOS resampling for better quality
resized_image = image.resize((256, 256), Image.Resampling.LANCZOS)

# Save the resized image
resized_image.save('output2_resized.png')