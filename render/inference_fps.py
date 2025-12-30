from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF, QThread
import time
from gui.ConfigManager import ConfigManager
from gui.widgets.colors import get_theme_manager

# Initialize managers
settings_manager = ConfigManager()
theme_manager = get_theme_manager(settings_manager)

REGION_WIDTH = 500 # This might need to be passed in or shared if it varies

class UpdateThread(QThread):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def run(self):
        while True:
            self.widget.update_position()
            time.sleep(0.5)  # 500ms interval

class FPSOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create update thread for position
        self.update_thread = UpdateThread(self)
        self.update_thread.start()

        self.inference_fps = 0.0
        self.capture_fps = 0.0
        # Re-introduce gradient attributes and timer
        self.gradient_offset = 0
        self.gradient_timer = QTimer(self)
        self.gradient_timer.timeout.connect(self.update_gradient)
        self.gradient_timer.start(50) # Animation speed
        self.resize(500, 200) # Ensure size is sufficient
        self.update_position()
        theme_manager.themeChanged.connect(self.update) # Update on theme change

    def update_position(self):
        visual_config = settings_manager.config.get("Visual", {})
        new_x = int(visual_config.get("fps_x", 604.0))
        new_y = int(visual_config.get("fps_y", 503.0))
        if (self.x(), self.y()) != (new_x, new_y):
            self.move(new_x, new_y)

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("fps", True):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_fps(painter)

    def draw_fps(self, painter):
        # Re-introduce gradient using PRIMARY and ACCENT colors
        gradient = QLinearGradient(QPointF(0, 0), QPointF(200, 0)) # Adjust size as needed
        gradient.setColorAt(0, theme_manager.get_color("PRIMARY"))
        gradient.setColorAt(0.5, theme_manager.get_color("ACCENT"))
        gradient.setColorAt(1, theme_manager.get_color("PRIMARY"))
        gradient.setSpread(QLinearGradient.ReflectSpread)
        gradient.setStart(QPointF(self.gradient_offset, 0))
        gradient.setFinalStop(QPointF(self.gradient_offset + 200, 0)) # Match size

        font = QFont("Arial", 16, QFont.Bold) # Consider theming the font later if needed
        painter.setFont(font)
        
        inference_text = f"Inference: {self.inference_fps:.1f} FPS"
        capture_text = f"Capture: {self.capture_fps:.1f} FPS"
        
        text_x = 10 # Draw relative to widget
        text_y = 30

        # Set the pen to use the animated gradient
        #painter.setPen(QPen(gradient, 2)) # Use gradient, adjust thickness if needed
        #painter.drawText(text_x, text_y, inference_text)
        #painter.drawText(text_x, text_y + 25, capture_text)
        print(inference_text)


    # Re-introduce update_gradient method
    def update_gradient(self):
        self.gradient_offset = (self.gradient_offset + 5) % 200 # Match gradient size
        self.update()

    def update_fps(self, inference_fps, capture_fps):
        self.inference_fps = float(inference_fps)
        self.capture_fps = float(capture_fps)
        self.update()
