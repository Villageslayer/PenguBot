import socket
import struct
import threading
import time
import random
import math
from win32api import GetSystemMetrics, GetAsyncKeyState

# ==========================================
# HARDWARE CONFIGURATION
# ==========================================
ESP32_IP = "192.168.1.24"
ESP32_PORT = 4210

# THE SECRET KEY (Must match ESP32 exactly)
# A random lookup table for high-speed XOR encryption
SECRET_KEY = [
    0x4A, 0x1F, 0xC3, 0x89, 0x2D, 0xE5, 0x7B, 0x90, 0x12, 0x66, 0xF4, 0xAB, 0x09, 0xDD, 0x5E, 0x33,
    0x81, 0x47, 0x9C, 0x22, 0xFA, 0x05, 0xE0, 0x6B, 0x18, 0xD2, 0xB7, 0x4F, 0x94, 0x3A, 0xC8, 0x71,
    0x56, 0x0E, 0xBF, 0xA3, 0x29, 0xD6, 0x8C, 0x14, 0x60, 0xF9, 0x3E, 0x77, 0xB2, 0x98, 0x41, 0x06,
    0xED, 0x53, 0xAA, 0x1B, 0xC5, 0x86, 0x2F, 0xD9, 0x74, 0x02, 0xB0, 0x6E, 0x95, 0x37, 0xF1, 0x24,
    0xCC, 0x59, 0x10, 0x84, 0xDB, 0x63, 0x0A, 0xA8, 0x44, 0xEF, 0x7D, 0x26, 0x91, 0x35, 0xBC, 0x68,
    0x17, 0xD4, 0x72, 0xFE, 0x51, 0x0D, 0x99, 0x2A, 0xC1, 0x8F, 0x48, 0xE6, 0x75, 0x32, 0xB9, 0x04,
    0xF6, 0x6D, 0x21, 0x9E, 0x5C, 0x07, 0xBB, 0x40, 0x83, 0xD0, 0x67, 0x2E, 0xE2, 0x79, 0x15, 0xCF,
    0x58, 0xA5, 0x3B, 0x93, 0x0F, 0xFB, 0x4D, 0x88, 0x1C, 0x70, 0xAE, 0x36, 0xE9, 0x64, 0x25, 0x9A,
    0x55, 0x82, 0x13, 0xC6, 0x3F, 0xF2, 0x7E, 0x2B, 0x97, 0x45, 0x08, 0xDA, 0x61, 0xE8, 0x34, 0xB6,
    0x03, 0xCB, 0x9F, 0x50, 0xA1, 0x19, 0x76, 0xE4, 0x8D, 0x23, 0xD5, 0x6A, 0x16, 0xAC, 0x7F, 0x46,
    0xF5, 0x20, 0x9B, 0x57, 0x0B, 0xC9, 0x80, 0x3D, 0xE1, 0x69, 0x1D, 0xB4, 0x78, 0x27, 0xDF, 0x54,
    0x96, 0x42, 0xEC, 0x7A, 0x11, 0xA6, 0x30, 0xF8, 0x65, 0xBE, 0xD7, 0x8E, 0x2C, 0x5F, 0x01, 0xCA,
    0x49, 0x92, 0x1A, 0xE3, 0x73, 0x38, 0xA9, 0x5D, 0xD1, 0x62, 0xB5, 0x0C, 0xFC, 0x85, 0x31, 0xAF,
    0x6C, 0x28, 0xF3, 0x7C, 0x9D, 0x4E, 0x1E, 0xB8, 0x52, 0xA0, 0x00, 0xCD, 0x8B, 0x43, 0xE7, 0x5B,
    0x39, 0xA2, 0x6F, 0xD8, 0x22, 0xEE, 0x87, 0x12, 0x5A, 0xBD, 0x74, 0x4C, 0x90, 0x3C, 0xF0, 0xA4,
    0xB1, 0x66, 0x05, 0xEB, 0x7B, 0x2F, 0x94, 0x47, 0xC4, 0x18, 0xAD, 0x5E, 0xD3, 0x8A, 0x2D, 0xFE
]


class MouseMover:
    """
    MouseMover with two movement systems:
    
    1. "classic" - Direct percentage-based movement (original behavior, fast)
    2. "spring" - Critically damped spring system (smooth, no oscillation)
    
    All parameters are fetched via callbacks so they update in real-time from settings.
    
    IMPORTANT: This does NOT use GetCursorPos() because in games like Valorant,
    the cursor is hidden and its position is meaningless. The crosshair is ALWAYS
    at screen center, and mouse movement is relative. We calculate movement as:
    target_position - screen_center
    """
    
    def __init__(self, settings_getter):
        """
        Initialize MouseMover.
        
        Args:
            settings_getter: A callable that takes a key path and default value,
                           returns the current setting value.
                           Example: lambda key, default: config_manager.get(key, default)
        """
        self.ip = ESP32_IP
        self.port = ESP32_PORT
        self.get_setting = settings_getter
        
        self.screen_width = GetSystemMetrics(0)
        self.screen_height = GetSystemMetrics(1)
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2

        # UDP Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sock.setblocking(False)

        # Protocol headers
        self.HEAD_MOVE = 0xAB
        self.HEAD_CLICK = 0xAC

        # Target position (in screen coordinates)
        self.target_x = float(self.center_x)
        self.target_y = float(self.center_y)
        self.has_target = False
        self.target_timeout = 0.1
        self.last_target_time = 0.0
        
        # Velocity for spring system
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # Accumulated sub-pixel movement
        self.accumulated_x = 0.0
        self.accumulated_y = 0.0
        
        # Thread synchronization
        self.running = True
        self.lock = threading.Lock()
        
        # Performance tracking
        self.last_move_time = time.perf_counter()
        
        # Start worker thread
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        
        print(f"[*] UDP Encrypted Mouse -> {self.ip}:{self.port}")

    def set_mouse_position(self, x, y):
        """Set the target position for the mouse to move towards (screen coordinates)."""
        with self.lock:
            self.target_x = float(max(0, min(x, self.screen_width - 1)))
            self.target_y = float(max(0, min(y, self.screen_height - 1)))
            self.has_target = True
            self.last_target_time = time.perf_counter()
    
    def clear_target(self):
        """Clear the current target - mouse will stop moving."""
        with self.lock:
            self.has_target = False

    def _encrypt_and_send(self, header, data1, data2=0):
        """
        FULL ENCRYPTION ENGINE - ALL BYTES ENCRYPTED
        """
        salt = random.randint(0, 255)
        
        key_header = SECRET_KEY[salt]
        key_data1 = SECRET_KEY[(salt + 73) % 256]
        key_data2 = SECRET_KEY[(salt + 149) % 256]
        key_check = SECRET_KEY[(salt + 211) % 256]
        
        enc_header = (header ^ key_header) & 0xFF
        enc_data1 = (data1 ^ key_data1) & 0xFF
        enc_data2 = (data2 ^ key_data2) & 0xFF
        
        checksum = (header ^ data1 ^ data2) & 0xFF
        enc_checksum = (checksum ^ key_check) & 0xFF
        
        try:
            packet = struct.pack('BBBBB', salt, enc_header, enc_data1, enc_data2, enc_checksum)
            self.sock.sendto(packet, (self.ip, self.port))
        except BlockingIOError:
            pass

    def click(self, button='left'):
        """Send a mouse click."""
        btn_code = 1 if button == 'left' else 2
        self._encrypt_and_send(self.HEAD_CLICK, btn_code, 0)

    def _calculate_classic_movement(self, target_x, target_y):
        """
        Classic movement system - direct and fast.
        
        Calculates movement needed to go from screen center (crosshair) to target.
        
        Settings used:
        - speed: Overall speed multiplier (0.0 - 1.0)
        - smoothing_factor: How much of the distance to cover per frame (0.1 - 1.0)
        - acceleration_factor: Speeds up movement when far from target (1.0 - 3.0)
        - min_speed_multiplier: Minimum pixels to move per frame when close (0.0 - 10.0)
        - max_speed_cap: Maximum pixels per movement (1 - 127)
        """
        speed = self.get_setting("Aimbot.speed", 0.1)
        smoothing = self.get_setting("Aimbot.smoothing_factor", 0.5)
        acceleration = self.get_setting("Aimbot.acceleration_factor", 1.5)
        min_speed = self.get_setting("Aimbot.min_speed_multiplier", 1.0)
        max_cap = int(self.get_setting("Aimbot.max_speed_cap", 127))
        
        # Calculate distance from screen center (crosshair) to target
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.5:
            return 0, 0
        
        # Base movement factor
        factor = smoothing * speed
        
        # Apply acceleration for distant targets (move faster when far)
        if distance > 50:
            accel_bonus = min(acceleration, 1.0 + (distance / 100.0) * (acceleration - 1.0))
            factor *= accel_bonus
        
        # Calculate movement
        move_x = dx * factor
        move_y = dy * factor
        move_dist = math.sqrt(move_x * move_x + move_y * move_y)
        
        # Enforce minimum speed - if movement is too small, scale it up
        # min_speed is the minimum pixels to move per frame
        if move_dist > 0 and move_dist < min_speed and distance >= min_speed:
            scale = min_speed / move_dist
            move_x *= scale
            move_y *= scale
            move_dist = min_speed
        
        # If we're closer than min_speed pixels, just move the remaining distance
        # (prevents overshooting)
        if distance < min_speed:
            move_x = dx
            move_y = dy
            move_dist = distance
        
        # Cap maximum movement
        if move_dist > max_cap:
            scale = max_cap / move_dist
            move_x *= scale
            move_y *= scale
        
        return move_x, move_y

    def _calculate_spring_movement(self, target_x, target_y, dt):
        """
        Spring-damper movement system - smooth with no oscillation.
        
        Calculates movement needed to go from screen center (crosshair) to target.
        
        Settings used:
        - speed: Scales the spring stiffness (0.0 - 1.0)
        - spring_stiffness: Base spring constant (50 - 500)
        - spring_damping: Damping ratio, 1.0 = critical damping (0.5 - 2.0)
        """
        speed = self.get_setting("Aimbot.speed", 0.1)
        stiffness = self.get_setting("Aimbot.spring_stiffness", 150.0)
        damping_ratio = self.get_setting("Aimbot.spring_damping", 1.0)
        
        # Clamp dt to prevent instability
        dt = min(dt, 0.05)
        if dt <= 0:
            dt = 0.001
        
        # Distance from screen center (crosshair) to target
        error_x = target_x - self.center_x
        error_y = target_y - self.center_y
        
        # Scale stiffness by speed setting
        k = stiffness * (0.5 + speed * 2.0)
        
        # Critical damping coefficient
        c = 2.0 * math.sqrt(k) * damping_ratio
        
        # Spring-damper acceleration
        accel_x = k * error_x - c * self.velocity_x
        accel_y = k * error_y - c * self.velocity_y
        
        # Update velocity
        self.velocity_x += accel_x * dt
        self.velocity_y += accel_y * dt
        
        # Calculate displacement
        dx = self.velocity_x * dt
        dy = self.velocity_y * dt
        
        # Settle when very close and slow
        distance = math.sqrt(error_x * error_x + error_y * error_y)
        vel_magnitude = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        
        if distance < 0.5 and vel_magnitude < 5.0:
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            return error_x, error_y
        
        return dx, dy

    def _worker_loop(self):
        """Main movement loop."""
        while self.running:
            loop_start_time = time.perf_counter()
            
            # Get settings
            target_fps = self.get_setting("Aimbot.fps", 165)
            if target_fps <= 0:
                target_fps = 165
            target_frame_time = 1.0 / target_fps
            
            trigger_key = int(self.get_setting("Aimbot.trigger_key", 0x05))
            movement_type = self.get_setting("Aimbot.movement_type", "classic")
            
            dt = loop_start_time - self.last_move_time
            
            # Check trigger key
            if not (GetAsyncKeyState(trigger_key) & 0x8000):
                # Not aiming - reset state
                self.velocity_x = 0.0
                self.velocity_y = 0.0
                self.accumulated_x = 0.0
                self.accumulated_y = 0.0
                self.has_target = False
                
                elapsed = time.perf_counter() - loop_start_time
                sleep_time = max(0.0005, target_frame_time - elapsed)
                time.sleep(sleep_time)
                self.last_move_time = loop_start_time
                continue
            
            # Check if we have a valid target
            with self.lock:
                has_valid_target = self.has_target
                target_age = loop_start_time - self.last_target_time
                
                if target_age > self.target_timeout:
                    has_valid_target = False
                    self.has_target = False
                
                tx, ty = self.target_x, self.target_y
            
            if not has_valid_target:
                # No target - don't move
                self.velocity_x = 0.0
                self.velocity_y = 0.0
                self.accumulated_x = 0.0
                self.accumulated_y = 0.0
                
                elapsed = time.perf_counter() - loop_start_time
                sleep_time = max(0.0005, target_frame_time - elapsed)
                time.sleep(sleep_time)
                self.last_move_time = loop_start_time
                continue
            
            # Calculate movement based on selected system
            # Movement is always: target - screen_center
            if movement_type == "spring":
                dx, dy = self._calculate_spring_movement(tx, ty, dt)
            else:  # classic
                dx, dy = self._calculate_classic_movement(tx, ty)
            
            # Accumulate sub-pixel movement
            self.accumulated_x += dx
            self.accumulated_y += dy
            
            # Extract integer pixels
            int_dx = int(self.accumulated_x)
            int_dy = int(self.accumulated_y)
            
            # Keep remainder
            self.accumulated_x -= int_dx
            self.accumulated_y -= int_dy
            
            # Clamp to valid range
            int_dx = max(-127, min(127, int_dx))
            int_dy = max(-127, min(127, int_dy))
            
            # Send movement
            if int_dx != 0 or int_dy != 0:
                dx_u = int_dx & 0xFF
                dy_u = int_dy & 0xFF
                self._encrypt_and_send(self.HEAD_MOVE, dx_u, dy_u)
            
            self.last_move_time = loop_start_time
            
            # Sleep to maintain target FPS
            elapsed = time.perf_counter() - loop_start_time
            sleep_time = target_frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        """Stop the mouse mover and clean up."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.sock.close()
        print("[*] MouseMover stopped")


# For testing
if __name__ == "__main__":
    print("MouseMover test mode")
    
    # Mock settings
    test_settings = {
        "Aimbot.speed": 0.5,
        "Aimbot.fps": 165,
        "Aimbot.trigger_key": 0x05,
        "Aimbot.movement_type": "classic",
        "Aimbot.smoothing_factor": 0.5,
        "Aimbot.acceleration_factor": 1.5,
        "Aimbot.min_speed_multiplier": 3.0,
        "Aimbot.max_speed_cap": 127,
        "Aimbot.spring_stiffness": 150.0,
        "Aimbot.spring_damping": 1.0,
    }
    
    def get_setting(key, default):
        return test_settings.get(key, default)
    
    mover = MouseMover(settings_getter=get_setting)
    
    try:
        print("Testing movement... Press Ctrl+C to exit")
        print("Hold mouse button 4 (trigger) to test")
        
        center_x, center_y = 960, 540
        radius = 200
        angle = 0
        
        frame_time = 1.0 / test_settings["Aimbot.fps"]
        
        while True:
            loop_start = time.perf_counter()
            
            angle += 0.02
            target_x = center_x + radius * math.cos(angle)
            target_y = center_y + radius * math.sin(angle)
            mover.set_mouse_position(target_x, target_y)
            
            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mover.stop()