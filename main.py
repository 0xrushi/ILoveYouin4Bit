#!/usr/bin/env python3
"""
TUI App for Remote Control
- Left Arrow / 'a': Swipe Left
- Right Arrow / 'd': Swipe Right  
- 's': Take Screenshot
- 'q': Quit
"""

import curses
import requests
import threading
import time
from datetime import datetime
from frame_msg import FrameMsg, TxSprite
from PIL import Image
import asyncio
from pathlib import Path

async def display_image_on_frame(filename: str, frame: FrameMsg):
    """
    Displays the given indexed PNG image on the Frame display.

    Args:
        filename (str): Path to the indexed PNG image file.
        frame (FrameMsg): FrameMsg instance to use for communication.
    """
    try:
        await frame.print_short_text('Loading image...')
        
        await frame.upload_stdlua_libs(lib_names=['data', 'sprite'])
        await frame.upload_frame_app(local_filename="lua/sprite_frame_app.lua")
        frame.attach_print_response_handler()
        await frame.start_frame_app()

        # Load and send the sprite
        sprite = TxSprite.from_indexed_png_bytes(Path(filename).read_bytes())
        await frame.send_message(0x20, sprite.pack())

        # Keep image displayed (will be cleared when arrows are pressed)
        await asyncio.sleep(30.0)
        
    except asyncio.CancelledError:
        print("Image display cancelled")
    except Exception as e:
        print(f"An error occurred displaying image: {e}")
    finally:
        try:
            frame.detach_print_response_handler()
            await frame.stop_frame_app()
        except:
            pass

async def send_frame_status(frame: FrameMsg, message: str):
    """Send status message to frame display"""
    try:
        await frame.print_short_text(message)
    except Exception as e:
        print(f"Error sending frame status: {e}")

class TUIApp:
    def __init__(self):
        self.base_url = "http://10.0.0.204:1821"
        self.status_messages = []
        self.max_status_lines = 10
        self.frame = FrameMsg()
        self.frame_connected = False
        self.image_task = None
        self.loop = None
        self.async_thread = None
        
    def start_async_loop(self):
        """Start the async event loop in a separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.async_thread = threading.Thread(target=run_loop, daemon=True)
        self.async_thread.start()
        time.sleep(0.1)
        
    async def init_frame_connection(self):
        """Initialize frame connection"""
        try:
            await self.frame.connect()
            self.frame_connected = True
            await self.frame.print_short_text('TUI Remote Control Ready')
            self.add_status("✓ Frame connected successfully")
        except Exception as e:
            self.add_status(f"✗ Frame connection failed: {str(e)}")
            self.frame_connected = False

    
    def add_status(self, message):
        """Add a status message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_messages.append(f"[{timestamp}] {message}")
        if len(self.status_messages) > self.max_status_lines:
            self.status_messages.pop(0)
    
    def stop_current_image(self):
        """Stop currently displaying image on frame"""
        if self.image_task and not self.image_task.done():
            self.image_task.cancel()
            self.add_status("Image display stopped")
            # Send status to frame
            if self.frame_connected and self.loop:
                try:
                    asyncio.run_coroutine_threadsafe(
                        send_frame_status(self.frame, "Image cleared"),
                        self.loop
                    )
                except:
                    pass
    
    def take_screenshot(self):
        """Take screenshot and display on frame"""
        def screenshot_worker():
            try:
                url = f"{self.base_url}/screenshot"
                self.add_status("Taking screenshot...")
                
                if self.frame_connected and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        send_frame_status(self.frame, "Taking screenshot..."),
                        self.loop
                    )
                
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    # Save screenshot image to file
                    try:
                        with open("output.png", "wb") as f:
                            f.write(response.content)
                        self.add_status(f"✓ Screenshot saved to output.png")
                        
                        # Send status to frame
                        if self.frame_connected and self.loop:
                            asyncio.run_coroutine_threadsafe(
                                send_frame_status(self.frame, "Screenshot saved"),
                                self.loop
                            )
                        
                        img = Image.open("output.png")
                                                
                        img.thumbnail((350, 350), Image.LANCZOS)
                        img_4bit = img.convert('P', palette=Image.ADAPTIVE, colors=16)
                        
                        # use the scripts/cropper_experiment.py to decide the coordinates for your device
                        crop_box = (15, 39, 154, 276)
                        img_4bit = img_4bit.crop(crop_box)
                        
                        img_4bit_path = "output_4bit.png"
                        img_4bit.save(img_4bit_path)
                        self.add_status(f"✓ Converted to 4-bit and saved to {img_4bit_path}")
                        
                        if self.frame_connected and self.loop:
                            asyncio.run_coroutine_threadsafe(
                                send_frame_status(self.frame, "Converted to 4-bit"),
                                self.loop
                            )
                        
                        if self.frame_connected and self.loop:
                            try:
                                self.image_task = asyncio.run_coroutine_threadsafe(
                                    display_image_on_frame(img_4bit_path, self.frame),
                                    self.loop
                                )
                                self.add_status("✓ Image sent to Frame")
                            except Exception as e:
                                self.add_status(f"✗ Failed to display on Frame: {str(e)}")
                    except Exception as e:
                        self.add_status(f"✗ Failed to save screenshot: {str(e)}")
                        if self.frame_connected and self.loop:
                            asyncio.run_coroutine_threadsafe(
                                send_frame_status(self.frame, "Screenshot failed"),
                                self.loop
                            )
                else:
                    self.add_status(f"✗ Screenshot - Error {response.status_code}")
                    if self.frame_connected and self.loop:
                        asyncio.run_coroutine_threadsafe(
                            send_frame_status(self.frame, "Screenshot error"),
                            self.loop
                        )
            except requests.exceptions.RequestException as e:
                self.add_status(f"✗ Screenshot - Connection failed")
                if self.frame_connected and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        send_frame_status(self.frame, "Screenshot failed"),
                        self.loop
                    )
            except Exception as e:
                self.add_status(f"✗ Screenshot - Error: {str(e)}")
        
        thread = threading.Thread(target=screenshot_worker)
        thread.daemon = True
        thread.start()

    def swipe_and_screenshot(self, direction):
        """Swipe in direction and then take screenshot"""
        def swipe_screenshot_worker():
            try:
                # First make the swipe request
                swipe_url = f"{self.base_url}/swipe-{direction}"
                self.add_status(f"Sending swipe {direction}...")
                
                # Send status to frame
                if self.frame_connected and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        send_frame_status(self.frame, f"Swiping {direction}..."),
                        self.loop
                    )
                
                response = requests.get(swipe_url, timeout=5)
                
                if response.status_code == 200:
                    self.add_status(f"✓ Swipe {direction} - Success")
                    if self.frame_connected and self.loop:
                        asyncio.run_coroutine_threadsafe(
                            send_frame_status(self.frame, f"Swipe {direction} done"),
                            self.loop
                        )
                    
                    time.sleep(0.5)
                    self.take_screenshot()
                    
                else:
                    self.add_status(f"✗ Swipe {direction} - Error {response.status_code}")
                    if self.frame_connected and self.loop:
                        asyncio.run_coroutine_threadsafe(
                            send_frame_status(self.frame, f"Swipe {direction} error"),
                            self.loop
                        )
            except requests.exceptions.RequestException as e:
                self.add_status(f"✗ Swipe {direction} - Connection failed")
                if self.frame_connected and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        send_frame_status(self.frame, f"Swipe {direction} failed"),
                        self.loop
                    )
            except Exception as e:
                self.add_status(f"✗ Swipe {direction} - Error: {str(e)}")
        
        thread = threading.Thread(target=swipe_screenshot_worker)
        thread.daemon = True
        thread.start()
    
    def draw_ui(self, stdscr):
        """Draw the main UI"""
        height, width = stdscr.getmaxyx()
        
        stdscr.clear()
        
        title = "Remote Control TUI"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        instructions = [
            "",
            "Controls:",
            "  ← / A     - Swipe Left",
            "  → / D     - Swipe Right", 
            "  S         - Take Screenshot",
            "  Q         - Quit",
            "",
            f"Target: {self.base_url}",
            f"Frame: {'Connected' if self.frame_connected else 'Disconnected'}",
            "",
            "Status Log:"
        ]
        
        for i, line in enumerate(instructions):
            if i + 2 < height:
                if line.startswith("  "):
                    stdscr.addstr(i + 2, 2, line)
                elif line.startswith("Frame:"):
                    color = curses.color_pair(1) if self.frame_connected else curses.color_pair(2)
                    stdscr.addstr(i + 2, 0, line, color)
                else:
                    stdscr.addstr(i + 2, 0, line, curses.A_BOLD if line == "Controls:" or line == "Status Log:" else 0)
        
        status_start_line = len(instructions) + 2
        for i, msg in enumerate(self.status_messages):
            if status_start_line + i < height - 1:
                color = curses.A_NORMAL
                if "✓" in msg:
                    # green
                    color = curses.color_pair(1)
                elif "✗" in msg:
                    # red
                    color = curses.color_pair(2)
                
                # Truncate message if too long
                display_msg = msg[:width-2] if len(msg) > width-2 else msg
                stdscr.addstr(status_start_line + i, 2, display_msg, color)
        
        footer = "Press Q to quit"
        if height > 1:
            stdscr.addstr(height - 1, 0, footer, curses.A_DIM)
        
        stdscr.refresh()
    
    def run(self, stdscr):
        """Main application loop"""
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(100) # Refresh every 100ms
        
        self.start_async_loop()
        
        if self.loop:
            try:
                init_future = asyncio.run_coroutine_threadsafe(
                    self.init_frame_connection(), self.loop
                )
                init_future.result(timeout=5)  # Wait up to 5 seconds for connection
            except Exception as e:
                self.add_status(f"✗ Frame init failed: {str(e)}")
        
        self.add_status("TUI Remote Control started")
        self.add_status("Waiting for commands...")
        
        try:
            while True:
                self.draw_ui(stdscr)
                
                try:
                    key = stdscr.getch()
                    
                    if key == ord('q') or key == ord('Q'):
                        self.add_status("Shutting down...")
                        self.draw_ui(stdscr)
                        
                        time.sleep(0.5)
                        break
                    
                    elif key == curses.KEY_LEFT or key == ord('a') or key == ord('A'):
                        self.stop_current_image()
                        self.add_status("Swipe Left + Screenshot triggered")
                        self.swipe_and_screenshot("left")
                    
                    elif key == curses.KEY_RIGHT or key == ord('d') or key == ord('D'):
                        self.stop_current_image()  # Stop image display
                        self.add_status("Swipe Right + Screenshot triggered") 
                        self.swipe_and_screenshot("right")
                    
                    elif key == ord('s') or key == ord('S'):
                        self.add_status("Screenshot triggered")
                        self.take_screenshot()
                    
                    elif key != -1:
                        pass
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.add_status(f"Error: {str(e)}")
        
        finally:
            if self.loop and not self.loop.is_closed():
                try:
                    self.loop.call_soon_threadsafe(self.loop.stop)
                    if self.async_thread and self.async_thread.is_alive():
                        self.async_thread.join(timeout=1)
                except:
                    pass

def main():
    app = TUIApp()
    try:
        curses.wrapper(app.run)
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()