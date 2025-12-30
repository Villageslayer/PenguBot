from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from .colors import get_theme_manager # Use theme manager
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean, ScrollableSettingsWidget,
                                  SettingsKeybind, SettingsCollapsibleSection)
from gui.widgets.Header import HeaderWidget


class AimbotWidget(QWidget):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager() # Get theme manager instance
        self.config_manager = config_manager
        self.setVisible(False)
        self.move(86, 7)
        self.resize(607, 426)

        # Initialize UI
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(0)

        # Header
        self.header = HeaderWidget("Combat Configuration")
        self.layout.addWidget(self.header)

        # Create scroll area and its container widget
        # ScrollableSettingsWidget now handles its own theme updates
        scroll_area = ScrollableSettingsWidget(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)

        aimbot_label = QLabel("Aimbot Settings")
        aimbot_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold; margin-top: 10px;")
        container_layout.addWidget(aimbot_label)


        # General Section
        general_section = SettingsCollapsibleSection("General")
        container_layout.addWidget(general_section)

        toggle = SettingsBoolean("Aimbot Toggle", True)
        general_section.addWidget(toggle)
        self.config_manager.register_setting("Aimbot", "enabled", toggle)

        trigger_key = SettingsKeybind("Trigger Key", 0x02) # Default Right Click
        general_section.addWidget(trigger_key)
        self.config_manager.register_setting("Aimbot", "trigger_key", trigger_key)

        scout_macro_toggle = SettingsBoolean("Scout Macro", False) # Default to False
        general_section.addWidget(scout_macro_toggle)
        self.config_manager.register_setting("Aimbot", "scout_macro", scout_macro_toggle)

        # Targeting Section
        targeting_section = SettingsCollapsibleSection("Targeting")
        container_layout.addWidget(targeting_section)

        fov_slider = SettingsSlider("FOV", 100, 640, 500, allow_decimals=False)
        targeting_section.addWidget(fov_slider)
        self.config_manager.register_setting("Aimbot", "fov", fov_slider)

        aim_fov_slider = SettingsSlider("Aim FOV Size", 1, 350, 100, allow_decimals=False)
        targeting_section.addWidget(aim_fov_slider)
        self.config_manager.register_setting("Aimbot", "aim_fov", aim_fov_slider)

        targeting_mode = SettingsDropdown("Targeting Mode", ["Closest", "Confidence"])
        targeting_section.addWidget(targeting_mode)
        self.config_manager.register_setting("Aimbot", "targeting_mode", targeting_mode)

        target_slider_1 = SettingsSlider("Target Height (1)", 0.01, 1.0, 0.25, allow_decimals=True)
        targeting_section.addWidget(target_slider_1)
        self.config_manager.register_setting("Aimbot", "target_height_1", target_slider_1)

        target_slider_2 = SettingsSlider("Target Height (2)", 0.01, 1.0, 0.25, allow_decimals=True)
        targeting_section.addWidget(target_slider_2)
        self.config_manager.register_setting("Aimbot", "target_height_2", target_slider_2)
        
        target_stickiness = SettingsSlider("Target Stickiness", 0.1, 1, 0.7, allow_decimals=True)
        targeting_section.addWidget(target_stickiness)
        self.config_manager.register_setting("Aimbot", "target_stickiness", target_stickiness)

        # Motion Section
        motion_section = SettingsCollapsibleSection("Motion")
        container_layout.addWidget(motion_section)

        movement_type = SettingsDropdown("Movement Type", ["classic", "spring"])
        motion_section.addWidget(movement_type)
        self.config_manager.register_setting("Aimbot", "movement_type", movement_type)

        speed = SettingsSlider("Speed", 0.001 , 5.0, 0.085, allow_decimals=True)
        motion_section.addWidget(speed)
        self.config_manager.register_setting("Aimbot", "speed", speed)

        max_speed = SettingsSlider("Max Speed Cap", 10, 500, 127, allow_decimals=False)
        motion_section.addWidget(max_speed)
        self.config_manager.register_setting("Aimbot", "max_speed_cap", max_speed)
        
        min_speed = SettingsSlider("Min Speed Multiplier", 0.01, 1.0, 0.15, allow_decimals=True)
        motion_section.addWidget(min_speed)
        self.config_manager.register_setting("Aimbot", "min_speed_multiplier", min_speed)
        
        smoothing = SettingsSlider("Smoothing Factor", 0.01, 1.0, 0.5, allow_decimals=True)
        motion_section.addWidget(smoothing)
        self.config_manager.register_setting("Aimbot", "smoothing_factor", smoothing)

        acceleration = SettingsSlider("Acceleration Factor", 0.1, 5.0, 1.5, allow_decimals=True)
        motion_section.addWidget(acceleration)
        self.config_manager.register_setting("Aimbot", "acceleration_factor", acceleration)

        # Spring Mechanics (Sub-section logic or separate section)
        spring_section = SettingsCollapsibleSection("Spring Mechanics")
        container_layout.addWidget(spring_section)
        
        stiffness = SettingsSlider("Spring Stiffness", 10.0, 500.0, 150.0, allow_decimals=True)
        spring_section.addWidget(stiffness)
        self.config_manager.register_setting("Aimbot", "spring_stiffness", stiffness)

        damping = SettingsSlider("Spring Damping", 0.1, 10.0, 1.0, allow_decimals=True)
        spring_section.addWidget(damping)
        self.config_manager.register_setting("Aimbot", "spring_damping", damping)

        # Recoil Control Section
        recoil_section = SettingsCollapsibleSection("Recoil Control")
        container_layout.addWidget(recoil_section)

        recoil_slider = SettingsSlider("Recoil", 0.01, 1.1, 0.03, allow_decimals=True)
        recoil_section.addWidget(recoil_slider)
        self.config_manager.register_setting("Aimbot", "recoil", recoil_slider)

        max_recoil_slider = SettingsSlider("Max Recoil", 1.0, 5.0, 2.0, allow_decimals=True)
        recoil_section.addWidget(max_recoil_slider)
        self.config_manager.register_setting("Aimbot", "max_recoil", max_recoil_slider)



        # Add stretch to push all widgets to the top
        container_layout.addStretch()

        # Set the container as the scroll area's widget
        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

    def setup_connections(self):
        # Connect theme manager signal to update styles
        self.theme_manager.themeChanged.connect(self._update_styles)
        # Connect other signals as needed
        pass

    def _update_styles(self):
        """Update styles for this widget when the theme changes."""
        # print("AimbotWidget updating styles...") # Debug print
        
        # Header updates itself

        # Child settings widgets update themselves via their own connections/methods
        # Find the ScrollableSettingsWidget and tell it to update its scrollbar style
        scroll_area = self.findChild(ScrollableSettingsWidget)
        if scroll_area and hasattr(scroll_area, 'update_styles'):
            scroll_area.update_styles()
        self.update() # Trigger repaint if needed for this widget specifically

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)