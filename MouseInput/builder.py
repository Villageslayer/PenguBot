import os


def generate_build_bat_with_data():
  py_files = []
  cwd = os.getcwd()

  for root, dirs, files in os.walk(cwd):
    # Skip .venv and anything under it
    if ".venv" in dirs:
      dirs.remove(".venv")  # Prevents walk from descending into .venv

    for file in files:
      if file.endswith(".py"):
        full_path = os.path.join(root, file)
        py_files.append(full_path)

  if not py_files:
    print("No Python files found.")
    return

  with open('build.bat', 'w') as bat_file:
    bat_file.write("@echo off\n")
    bat_file.write("echo Building executables with PyInstaller...\n")

    for py_path in py_files:
      rel_path = os.path.relpath(py_path, cwd)
      py_dir = os.path.dirname(rel_path).replace("\\", "/")
      add_data_arg = f"--add-data \"{py_path};{py_dir if py_dir else '.'}\""
      bat_file.write(f"pyinstaller --onefile {add_data_arg} \"{py_path}\"\n")

    bat_file.write("echo Done!\n")

  print(f"Generated build.bat with {len(py_files)} entries (excluding .venv).")
  for f in py_files:
    print(f" - {f}")


if __name__ == "__main__":
  generate_build_bat_with_data()
