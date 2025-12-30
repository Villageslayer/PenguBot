from typing import Any

from MouseInput.InputMethods.InputMethodGFCK import InputMethodGFCK
from MouseInput.InputMethods.InputMethodGhubMouse import InputMethodGhubMouse
from MouseInput.InputMethods.InputMethodArduino import InputMethodArduino
from MouseInput.InputMethods.InputMethod import InputMethod
from MouseInput.InputMethods.InputMethodKmBox import InputMethodKmBox
from MouseInput.InputMethods.InputMethodKmBoxNet import InputMethodKmBoxNet
from MouseInput.InputMethods.InputMethodWin32 import InputMethodWin32


class MouseInput:
  InputMethodGFCK = InputMethodGFCK
  InputMethodArduino = InputMethodArduino
  InputMethodKmBox = InputMethodKmBox
  InputMethodKmBoxNet = InputMethodKmBoxNet
  InputMethodWin32 = InputMethodWin32
  InputMethodGhubMouse = InputMethodGhubMouse
  INIT_METHOD = InputMethodGFCK

  def __init__(self):
    self.ip = None
    self.port = None
    self.uuid = None
    self.input_methods = [InputMethodGFCK, InputMethodGhubMouse, #GFCK
                          InputMethodArduino, InputMethodKmBox, # Arduino,KmBox
                          InputMethodKmBoxNet, InputMethodWin32] # KmBoxNet, Win32
    self.current_input_method: InputMethod = self.INIT_METHOD()

  def set_connection(self, ip: str, port: int, uuid: str):
    """Set the connection parameters for the KmBoxNet device."""
    self.uuid = uuid
    self.ip = ip
    self.port = port
    if self.current_input_method == InputMethodKmBoxNet:
      self.current_input_method.set_connection(ip, port, uuid)


  def get_input_methods(self) -> list[Any]:
    rtn = list()
    for input_method in self.input_methods:
      rtn.append(input_method.NAME)
    return rtn

  def get_current_input_method(self):
    return self.current_input_method.NAME

  def set_current_input_method(self, input_method: str):
    if input_method in self.get_input_methods():
      match input_method:
        case self.InputMethodGFCK.NAME:
          self.current_input_method = self.InputMethodGFCK()
        case self.InputMethodGhubMouse.NAME:
          self.current_input_method = self.InputMethodGhubMouse()
        case self.InputMethodArduino.NAME:
          self.current_input_method = self.InputMethodArduino()
        case self.InputMethodKmBox.NAME:
          self.current_input_method = self.InputMethodKmBox()
        case self.InputMethodKmBoxNet.NAME:
          self.current_input_method = self.InputMethodKmBoxNet(ip=self.ip,port=self.port,uuid=self.uuid)
        case self.InputMethodWin32.NAME:
          self.current_input_method = self.InputMethodWin32()

  def down(self, button):
    self.current_input_method.down(button)

  def up(self, button):
    self.current_input_method.up(button)

  def click(self, button):
    self.current_input_method.click(button)

  def moveRelative(self, x, y):
    self.current_input_method.moveRelative(x, y)
