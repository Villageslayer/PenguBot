import time
import time
import bettercam
import cv2
import cv2
from render.inference_fps import FPSOverlay
from render.capture import ScreenCapture
from render.fov import FOVOverlay, AimFOVOverlay
from win32api import GetSystemMetrics
from ObjectDetector import FastObjectDetector
from gui.widgets.colors import theme_manager # Import theme_manager instead of Colors
from mouse_mover import MouseMover
import win32api
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPointF
import threading
from queue import Queue, Empty, Full
import json
from pathlib import Path
from gui.ConfigManager import ConfigManager
import numpy as np

# Initialize config manager at module level
settings_manager = ConfigManager()
# Ensure theme manager loads theme from config *before* widgets are created
from gui.widgets.colors import get_theme_manager
get_theme_manager(settings_manager)


# Screen dimensions
REGION_WIDTH = 500
REGION_HEIGHT = REGION_WIDTH
LEFT = (GetSystemMetrics(0) - REGION_WIDTH) // 2
TOP = (GetSystemMetrics(1) - REGION_HEIGHT) // 2
RIGHT = LEFT + REGION_WIDTH
BOTTOM = TOP + REGION_HEIGHT

multiplier = 0.12

# UpdateThread and associated classes moved to render.inference_fps

# Why ? Bettercam has this built in.
class FrameRingBuffer:
    def __init__(self, buffer_size=3, frame_shape=None):
        self.size = buffer_size
        self.frame_shape = frame_shape
        self.buffer = [None] * buffer_size if frame_shape is None else np.zeros((buffer_size, *frame_shape), dtype=np.uint8)
        self.write_idx = 0
        self.read_idx = 0
        self._lock = threading.Lock()
        self.frames_processed = 0
        self.frames_dropped = 0

    def put_frame(self, frame):
        if self.frame_shape is None and frame is not None:
            self.frame_shape = frame.shape
            self.buffer = np.zeros((self.size, *self.frame_shape), dtype=np.uint8)

        with self._lock:
            next_write = (self.write_idx + 1) % self.size
            if next_write == self.read_idx:
                self.read_idx = (self.read_idx + 1) % self.size
                self.frames_dropped += 1
            np.copyto(self.buffer[self.write_idx], frame)
            self.write_idx = next_write
            self.frames_processed += 1

    def get_latest_frame(self):
        with self._lock:
            if self.write_idx == self.read_idx:
                return None, -1
            prev_write = (self.write_idx - 1) % self.size
            # Return frame AND the processed count as a sequence ID
            return self.buffer[prev_write].copy(), self.frames_processed

# FPSOverlay moved to render.inference_fps
# FOVOverlay moved to render.fov

# Note:
# Not on Git for some reason
# FPSOverlay moved to render.inference_fps


class DetectionOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detection Overlay")
        self.setGeometry(LEFT, TOP, REGION_WIDTH, REGION_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.circle_positions = []
        theme_manager.themeChanged.connect(self.update) # Update on theme change

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("target", False):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Use theme_manager.get_color() which returns a QColor
        painter.setPen(QPen(theme_manager.get_color("AIM_INDICATOR"), 7))
        for pos in self.circle_positions:
            painter.drawEllipse(QPointF(pos[0], pos[1]), 5, 5)

    def update_circles(self, positions):
        self.circle_positions = positions
        self.update()


key_states = {
    0x31: False,  # Key '1'
    0x32: False,  # Key '2'
}

# Variables for smooth aim height adjustment
left_click_held = False
original_multiplier = None

# Create a function to update settings when config changes
def update_settings_from_config():
    global multiplier, original_multiplier
    # If we're not in midst of recoil adjustment, update multiplier to current setting
    if not left_click_held:
        if win32api.GetAsyncKeyState(0x31) < 0:
            new_mult = settings_manager.get("Aimbot.target_height_1", 0.18)
            multiplier = new_mult
            original_multiplier = new_mult
        elif win32api.GetAsyncKeyState(0x32) < 0:
            new_mult = settings_manager.get("Aimbot.target_height_2", 0.11)
            multiplier = new_mult
            original_multiplier = new_mult


# Register the observer with the settings manager to be notified of changes
settings_manager.register_observer(update_settings_from_config)


def update_multiplier():
    global multiplier, left_click_held, original_multiplier

    target_height_1 = settings_manager.get("Aimbot.target_height_1", 0.18)
    target_height_2 = settings_manager.get("Aimbot.target_height_2", 0.11)
    base_height_increment = settings_manager.get("Aimbot.recoil", 0.03)

    # Handle key 1 press (toggle, not hold)
    if win32api.GetAsyncKeyState(0x31) < 0 and not key_states[0x31]:
        multiplier = target_height_1
        original_multiplier = target_height_1  # Also update original to prevent recoil reset issues
        key_states[0x31] = True
    elif win32api.GetAsyncKeyState(0x31) >= 0:
        key_states[0x31] = False

    # Handle key 2 press (toggle, not hold)
    if win32api.GetAsyncKeyState(0x32) < 0 and not key_states[0x32]:
        multiplier = target_height_2
        original_multiplier = target_height_2  # Also update original to prevent recoil reset issues
        key_states[0x32] = True
    elif win32api.GetAsyncKeyState(0x32) >= 0:
        key_states[0x32] = False

    trigger_key = settings_manager.get("Aimbot.trigger_key", 0x05)
    
    right_click_held = (win32api.GetAsyncKeyState(trigger_key) & 0x8000) != 0
    left_click_current = (win32api.GetAsyncKeyState(0x01) & 0x8000) != 0

    if not right_click_held:
        # Reset recoil state when not aiming
        if left_click_held and original_multiplier is not None:
            multiplier = original_multiplier
        original_multiplier = None
        left_click_held = False
        return

    current_speed = settings_manager.get("Aimbot.speed", 0.08)
    height_increment = base_height_increment * current_speed

    if left_click_current:
        if not left_click_held:
            # Just started shooting - save current multiplier
            left_click_held = True
            original_multiplier = multiplier

        if original_multiplier is not None:
            max_recoil_factor = settings_manager.get("Aimbot.max_recoil", 2.0)
            max_value = original_multiplier * max_recoil_factor
            multiplier = min(multiplier + height_increment, max_value)

    elif left_click_held:
        # Just released left click - restore original multiplier
        left_click_held = False
        if original_multiplier is not None:
            multiplier = original_multiplier
        original_multiplier = None

def frame_producer(capture, frame_buffer):
    while True:
        frame = capture.get_latest_frame()
        if frame is not None:
            frame_buffer.put_frame(frame)
        time.sleep(0.001)  # Small sleep to prevent CPU thrashing

def main():
    app = QApplication([])
    detection_overlay = DetectionOverlay()
    fps_overlay = FPSOverlay()
    fov_overlay = FOVOverlay(REGION_WIDTH, REGION_HEIGHT, LEFT, TOP, settings_manager)
    aim_fov_overlay = AimFOVOverlay(REGION_WIDTH, REGION_HEIGHT, LEFT, TOP, settings_manager)
    detection_overlay.show()
    fps_overlay.show()
    fov_overlay.show()
    aim_fov_overlay.show()

    # Mouse movement setup with larger queue
    mouse_movement_queue = Queue(maxsize=1)

    def mouse_movement_worker():
        mouse = MouseMover(
            settings_getter=lambda key, default: settings_manager.get(key, default)
        )
        last_position = None
        while True:
            try:
                position = mouse_movement_queue.get(timeout=0.001)
                trigger_key = settings_manager.get("Aimbot.trigger_key", 0x05)
                if ((win32api.GetAsyncKeyState(trigger_key) & 0x8000) != 0 and
                        (last_position is None or position != last_position)):
                    mouse.set_mouse_position(*position)
                    last_position = position
            except Empty:
                continue
            except Exception as e:
                print(f"Mouse movement error: {e}")

    movement_thread = threading.Thread(target=mouse_movement_worker, daemon=True)
    movement_thread.start()

    try:
        current_model_name = settings_manager.get("AI.model", "csgo2_best.engine")
        detector = FastObjectDetector(engine_path='assets/models/' + current_model_name)
        
        # Model reload state
        model_reload_state = {
            "needed": False,
            "new_model_name": None
        }

        def check_model_change():
            new_name = settings_manager.get("AI.model", "csgo2_best.engine")
            if new_name != current_model_name:
                model_reload_state["needed"] = True
                model_reload_state["new_model_name"] = new_name

        settings_manager.register_observer(check_model_change)

        region = (LEFT, TOP, RIGHT, BOTTOM)
        target_fps = int(settings_manager.get("Aimbot.fps", 999))
        capture = ScreenCapture(region=region, output_idx=0, output_color="BGRA", target_fps=target_fps)
        capture.start()

        # Initialize frame buffer with size 3
        frame_buffer = FrameRingBuffer(buffer_size=3)

        # Start frame producer thread
        producer_thread = threading.Thread(target=frame_producer, args=(capture, frame_buffer), daemon=True)
        producer_thread.start()

        frame_count = 0
        last_fps_time = time.time()
        update_gui_counter = 0  # Counter for GUI updates

        last_processed_seq_id = -1
        
        # Target tracking for sticky aiming
        current_target_box = None

        while True:
            frame, seq_id = frame_buffer.get_latest_frame()
            if frame is None:
                continue

            # Check if we should cap inference FPS
            if settings_manager.get("AI.cap_inference_fps", False):
                if seq_id <= last_processed_seq_id:
                    time.sleep(0.0001) # Sleep briefly to yield
                    continue
            
            last_processed_seq_id = seq_id
            
            # Check for model reload
            if model_reload_state["needed"]:
                new_name = model_reload_state["new_model_name"]
                if new_name:
                    print(f"Switching model to {new_name}...")
                    if detector.reload('assets/models/' + new_name):
                        current_model_name = new_name
                    model_reload_state["needed"] = False

            current_time = time.time()
            update_multiplier()

            # Process frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            boxes = detector.detect(frame_rgb)

            # Find best target with sticky tracking
            circle_positions = []
            if boxes:
                # In FPS games, crosshair is always at center (mouse is relative)
                center_x_norm = 0.5
                center_y_norm = 0.5
                aim_fov_radius = settings_manager.get("Aimbot.aim_fov", 100.0)
                normalized_radius_sq = (aim_fov_radius / REGION_WIDTH) ** 2
                
                # 1. Collect ALL detections for overlay display
                for box in boxes:
                    x1, y1, x2, y2 = box['bbox']
                    x1_abs, y1_abs = x1 * REGION_WIDTH, y1 * REGION_HEIGHT
                    x2_abs, y2_abs = x2 * REGION_WIDTH, y2 * REGION_HEIGHT
                    
                    circle_x = int((x1_abs + x2_abs) / 2)
                    circle_y = int(y1_abs + (y2_abs - y1_abs) * multiplier)
                    circle_positions.append((circle_x, circle_y))

                # 2. Find best target WITHIN Aim FOV
                # Target stickiness threshold - require this much closer before switching
                # (as a ratio, e.g., 0.7 means new target must be 70% of current distance)
                stickiness = settings_manager.get("Aimbot.target_stickiness", 0.7)
                
                best_box = None
                best_distance_sq = float('inf')
                
                for box in boxes:
                    x1, y1, x2, y2 = box['bbox']
                    box_center_x = (x1 + x2) / 2
                    box_aim_y = y1 + (y2 - y1) * multiplier
                    
                    # Aim FOV Check: if ANY pixel of bbox is within the circle
                    # Simplest check: check if the distance from circle center to the closest point in the bbox is <= radius
                    # Coordinates are normalized [0, 1]
                    closest_x = max(x1, min(center_x_norm, x2))
                    closest_y = max(y1, min(center_y_norm, y2))
                    dist_to_center_sq = (closest_x - center_x_norm)**2 + (closest_y - center_y_norm)**2
                    
                    if dist_to_center_sq > normalized_radius_sq:
                        continue # Outside Aim FOV
                    
                    # Distance from crosshair (center) to aim point
                    distance_sq = (box_center_x - center_x_norm) ** 2 + (box_aim_y - center_y_norm) ** 2
                    
                    if distance_sq < best_distance_sq:
                        best_distance_sq = distance_sq
                        best_box = box
                
                # 3. Apply stickiness - check if we should keep current target
                # ENFORCE Aim FOV even for sticky targets
                if current_target_box is not None:
                    prev_box = current_target_box
                    # Find if previous target still exists (by checking overlap)
                    for box in boxes:
                        bx1, by1, bx2, by2 = box['bbox']
                        px1, py1, px2, py2 = prev_box['bbox']
                        
                        # Check if boxes overlap significantly (same target)
                        overlap_x = max(0, min(bx2, px2) - max(bx1, px1))
                        overlap_y = max(0, min(by2, py2) - max(by1, py1))
                        box_area = (bx2 - bx1) * (by2 - by1)
                        overlap_area = overlap_x * overlap_y
                        
                        if box_area > 0 and overlap_area / box_area > 0.3:
                            # Previous target still exists
                            # CRITICAL: Re-check Aim FOV for this specific box
                            closest_x = max(bx1, min(center_x_norm, bx2))
                            closest_y = max(by1, min(center_y_norm, by2))
                            dist_to_center_sq = (closest_x - center_x_norm)**2 + (closest_y - center_y_norm)**2
                            
                            if dist_to_center_sq <= normalized_radius_sq:
                                box_center_x = (bx1 + bx2) / 2
                                box_aim_y = by1 + (by2 - by1) * multiplier
                                prev_distance_sq = (box_center_x - center_x_norm) ** 2 + (box_aim_y - center_y_norm) ** 2
                                
                                # Only switch if new target is significantly closer
                                if best_distance_sq >= prev_distance_sq * stickiness:
                                    # Keep current target
                                    best_box = box
                                    best_distance_sq = prev_distance_sq
                            break # Found physical target, stop looking in current frames
                
                # Store current target for next frame
                current_target_box = best_box
                
                if best_box:
                    x1, y1, x2, y2 = best_box['bbox']
                    circle_x = int((x1 * REGION_WIDTH + x2 * REGION_WIDTH) / 2)
                    circle_y = int(y1 * REGION_HEIGHT + (y2 * REGION_HEIGHT - y1 * REGION_HEIGHT) * multiplier)

                    screen_x = LEFT + circle_x
                    screen_y = TOP + circle_y

                    trigger_key = settings_manager.get("Aimbot.trigger_key", 0x05)
                    if (win32api.GetAsyncKeyState(trigger_key) & 0x8000) != 0:
                        try:
                            mouse_movement_queue.put_nowait((screen_x, screen_y))
                        except Full:
                            pass
            else:
                # No detections - clear current target
                current_target_box = None

            # Update GUI less frequently (every 2 frames)
            update_gui_counter += 1
            if update_gui_counter >= 2:
                detection_overlay.update_circles(circle_positions)
                update_gui_counter = 0

            # FPS counter
            frame_count += 1
            elapsed_time = current_time - last_fps_time
            if elapsed_time >= 0.5:  # Update FPS every 500ms instead of every second
                fps = frame_count / elapsed_time
                capture_fps = capture.get_fps()
                fps_overlay.update_fps(fps, capture_fps)
                frame_count = 0
                last_fps_time = current_time

            # Process Qt events in batches
            if update_gui_counter == 0:
                app.processEvents()

    except KeyboardInterrupt:
        print("\nStopping gracefully...")
    finally:
        capture.stop()
        del capture

if __name__ == "__main__":
    main()