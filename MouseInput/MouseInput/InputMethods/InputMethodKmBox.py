import serial
import serial.tools.list_ports
from MouseInput.InputMethods.InputMethod import InputMethod

def list_ports():
  ports = serial.tools.list_ports.comports()
  for port in ports:
    print(port.description)
    if "CH340" in port.description:
      return port.device
  return None

class InputMethodKmBox(InputMethod):
  NAME: str = "KmBox"

  def __init__(self):
    super().__init__()
    self.kmbox_port = list_ports()  # Check your com port in windows device
    self.kmbox_baud_rate = 115200
    self.kmbox = None
    try:
      self.kmbox = serial.Serial(self.kmbox_port, self.kmbox_baud_rate)

      print('[INFO] kmbox connected on {}'.format(self.kmbox_port))
    except Exception as e:
      print(f'[ERROR] Could not connect to kmbox. {e}')
      self.close_connection()

  def __del__(self):
    try:
      self.close_connection()
    except Exception:
      pass

  def down(self, button):
    ...

  def up(self, button):
    ...

  def click(self, button):
    self.send_kmbox_command(f"km.click(0)")

  def moveRelative(self, x, y):
    self.send_kmbox_command(f"km.move({x},{y})")

  def send_kmbox_command(self, command):
    self.kmbox.write((command + '\r\n').encode())

  def close_connection(self):
    if self.kmbox is not None:
      self.kmbox.close()

if __name__ == '__main__':
  from time import sleep
  kmbox = InputMethodKmBox()
  sleep(0.001)
  for i in range(10):
    kmbox.moveRelative(10, 10)
    sleep(0.001)
    print("moving")