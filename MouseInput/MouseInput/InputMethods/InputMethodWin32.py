from MouseInput.InputMethods.InputMethod import InputMethod
from time import sleep
from typing import override
from win32api import mouse_event

class InputMethodWin32(InputMethod):
  NAME: str = "Win32"

  def __init__(self):
    super().__init__()


  @override
  def down(self, button):
    if button == 0:
      mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    elif button == 1:
      mouse_event(0x0008, 0, 0, 0, 0)  # RIGHTDOWN
    elif button == 2:
      mouse_event(0x0020, 0, 0, 0, 0)  # MIDDLEDOWN

  @override
  def up(self, button):
    if button == 0:
      mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
    elif button == 1:
      mouse_event(0x0010, 0, 0, 0, 0)  # RIGHTUP
    elif button == 2:
      mouse_event(0x0040, 0, 0, 0, 0)  # MIDDLEUP

  @override
  def click(self, button):
    self.down(button)
    sleep(0.1)
    self.up(button)

  @override
  def moveRelative(self, x, y):
    mouse_event(0x0001, x, y, 0, 0)  # MOVE
