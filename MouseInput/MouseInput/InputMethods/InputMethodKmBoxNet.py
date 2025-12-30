from typing import override

from MouseInput.InputMethods.InputMethod import InputMethod
from kmboxnet import KmboxNet
from time import sleep


class InputMethodKmBoxNet(InputMethod):
  NAME: str = "KmBoxNet"

  @override
  def __init__(self, **kwargs):
    """Initialize the KmBoxNet input method.
    :keyword ip: The IP address of the KmBoxNet device.
    :keyword port: The port number of the KmBoxNet device.
    :keyword uuid: The UUID of the KmBoxNet device.
    """
    super().__init__()
    self.ip = None if not "ip" in kwargs else kwargs["ip"]
    self.port = None if not "port" in kwargs else kwargs["port"]
    self.uuid = None if not "uuid" in kwargs else kwargs["uuid"]
    if not all([self.ip, self.port, self.uuid]):
      print("use set_connection(ip:str, port:int, uuid:str) to set connection parameters later.")
      return
    try:
      self.km = KmboxNet(self.ip, self.port, self.uuid)
    except Exception as e:
      print(f'[ERROR] Could not connect to KmBoxNet. {e}')
      raise e

  @override
  def set_connection(self, ip: str, port: int, uuid: str):
    """Set the connection parameters for the KmBoxNet device."""
    super().set_connection(ip, port, uuid)
    print("[INFO] Connecting to KmBoxNet... with ip:{}, port:{}, uuid:{}".format(ip, port, uuid))
    self.km = KmboxNet(self.ip, self.port, self.uuid)

  @override
  def down(self, button: int):
    match button:
      case 1:
        self.km.left(True)
      case 2:
        self.km.right(True)
      case 3:
        self.km.middle(True)

  @override
  def up(self, button: int):
    match button:
      case 1:
        self.km.left(False)
      case 2:
        self.km.right(False)
      case 3:
        self.km.middle(False)

  @override
  def click(self, button: int):
    self.down(button)
    sleep(0.1)
    self.up(button)

  @override
  def moveRelative(self, x: int, y: int):
    self.km.move(int(x), int(y))


if __name__ == '__main__':
  from time import sleep

  try:
    # Initialization is the only part that can raise a critical exception
    kmbox = InputMethodKmBoxNet(ip="192.168.2.188", port=49152, uuid="D6843CAB")

    print("🎉 Connected to Kmbox!")
    kmbox.down(1)
    kmbox.km.move(100, 100)
    sleep(0.5)
    kmbox.up(1)
    print("✅ Test completed successfully.")

  except Exception as e:
    print(f"Failed to connect: {e}")
    # Exit if connection fails, as nothing else will work
    exit()
