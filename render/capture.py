import bettercam
import time
import threading

class ScreenCapture:
    def __init__(self, region=None, output_idx=0, output_color="BGRA", target_fps=999):
        self.camera = bettercam.create(output_idx=output_idx, output_color=output_color, region=region)
        self.target_fps = target_fps
        self.running = False
        self.fps = 0.0
        self._frame_count = 0
        self._start_time = time.time()
        self._lock = threading.Lock()

    def start(self):
        if not self.running:
            self.camera.start(target_fps=self.target_fps, video_mode=True)
            self.running = True
            self._start_fps_timer()

    def _start_fps_timer(self):
        threading.Thread(target=self._fps_loop, daemon=True).start()

    def _fps_loop(self):
        while self.running:
            start_time = time.time()
            start_count = self._frame_count
            time.sleep(1.0)
            end_count = self._frame_count
            
            with self._lock:
                self.fps = (end_count - start_count) / (time.time() - start_time)

    def stop(self):
        if self.running:
            self.camera.stop()
            self.running = False
            
    def get_latest_frame(self):
        if self.running:
            frame = self.camera.get_latest_frame()
            if frame is not None:
                self._frame_count += 1
            return frame
        return None
    
    def get_fps(self):
        return self.fps

    def __del__(self):
        self.stop()
