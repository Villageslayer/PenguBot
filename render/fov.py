from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPointF
from gui.widgets.colors import theme_manager
from gui.ConfigManager import ConfigManager

# Initialize config manager at module level
settings_manager = ConfigManager()

class FOVOverlay(QWidget):
    def __init__(self, region_width, region_height, left, top, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.region_width = region_width
        self.region_height = region_height
        self.setWindowTitle("FOV Overlay")
        self.setGeometry(left, top, region_width, region_height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        theme_manager.themeChanged.connect(self.update) # Update on theme change
        self.settings_manager.register_observer(self.update) # Update on settings change

    def paintEvent(self, event):
        if not self.settings_manager.config.get("Visual", {}).get("fov", True):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        border_color = theme_manager.get_color("PRIMARY")
        border_color.setAlpha(80)
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(0, 0, self.region_width, self.region_height)

class AimFOVOverlay(QWidget):
    def __init__(self, region_width, region_height, left, top, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.region_width = region_width
        self.region_height = region_height
        self.setWindowTitle("Aim FOV Overlay")
        self.setGeometry(left, top, region_width, region_height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        theme_manager.themeChanged.connect(self.update) # Update on theme change
        self.settings_manager.register_observer(self.update) # Update on settings change

    def paintEvent(self, event):
        visual_config = self.settings_manager.config.get("Visual", {})
        if not visual_config.get("aim_fov", True):
            return
            
        aimbot_config = self.settings_manager.config.get("Aimbot", {})
        radius = aimbot_config.get("aim_fov", 100.0)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Use ACCENT color for Aim FOV to distinguish from Capture FOV
        circle_color = theme_manager.get_color("ACCENT")
        circle_color.setAlpha(120)
        
        painter.setPen(QPen(circle_color, 2))
        
        # Center of the capture region
        center_x = self.region_width / 2
        center_y = self.region_height / 2
        
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
