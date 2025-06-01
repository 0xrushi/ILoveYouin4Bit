import asyncio
from pathlib import Path

from frame_msg import FrameMsg, TxSprite

async def display_image(filename: str):
    """
    Displays the given indexed PNG image on the Frame display.

    Args:
        filename (str): Path to the indexed PNG image file.
    """
    frame = FrameMsg()
    try:
        await frame.connect()
        await frame.print_short_text('Loading...')
        await frame.upload_stdlua_libs(lib_names=['data', 'sprite'])
        await frame.upload_frame_app(local_filename="lua/sprite_frame_app.lua")
        frame.attach_print_response_handler()
        await frame.start_frame_app()

        sprite = TxSprite.from_indexed_png_bytes(Path(filename).read_bytes())
        await frame.send_message(0x20, sprite.pack())

        await asyncio.sleep(30.0)
        frame.detach_print_response_handler()
        await frame.stop_frame_app()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await frame.disconnect()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python display_image.py <image_filename>")
    else:
        asyncio.run(display_image(sys.argv[1]))