from MouseInput.InputMethods.InputMethod import InputMethod
from typing import override
from time import sleep
import ctypes
import os

class InputMethodGhubMouse(InputMethod):
  NAME:str = "GhubMouse"
  def __init__(self):
    super().__init__()
    current_dir = os.path.dirname(__file__)
    dll_path = os.path.join(current_dir, './Lib/ghub_mouse.dll')
    self.dll = ctypes.CDLL(dll_path)
    self.isOpen:bool = self.dll.mouse_open()

  def __del__(self):
      if self.isOpen: 
        self.dll.mouse_close()

  @override
  def down(self, button):
    self.dll.mouse_move(button, 0, 0, 0)

  @override
  def up(self, button):
    self.dll.mouse_move(0, 0, 0, 0)

  @override
  def click(self, button):
    self.down(button)
    sleep(0.1)
    self.up(button)

  @override
  def moveRelative(self,x,y):
    self.dll.moveR(x, y)

  def __call__(self, *args, **kwargs):
    """

    :param args: button,x,y,wheel
    :param kwargs:
    :return:
    """
    self.dll.mouse_move(*args)