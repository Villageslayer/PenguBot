from MouseInput.MouseInput import MouseInput

# Press the green button in the gutter to run the script.
def main():

    mouse_input = MouseInput()
    methods = mouse_input.get_input_methods()
    methods_str = ", ".join([f"{i}: {methods[i]}" for i in range(len(methods))])
    print(f"Methods {methods_str}")
    inp = input("Pick a Method to test ")
    if methods[int(inp)] == "KmBoxNet":
      mouse_input.set_connection(ip="192.168.2.188", port=49152, uuid="D6843CAB")
    mouse_input.set_current_input_method(methods[int(inp)])
    print("=== Current Input Method ===")
    print(mouse_input.get_current_input_method())

    input("Press Enter to Move the Mouse...")
    mouse_input.moveRelative(100, 100)
    input("Press Enter to Exit")
if __name__ == '__main__':
    main()

