# main.py
import sys
import os
import argparse
from emulator import ShellEmulatorGUI
import tkinter as tk
from tkinter import ttk

def parse_config():
    parser = argparse.ArgumentParser(description="Эмулятор оболочки ОС с VFS")
    parser.add_argument('--vfs', type=str, help='Путь к ZIP-архиву виртуальной ФС')
    parser.add_argument('--script', type=str, help='Путь к стартовому скрипту')
    parser.add_argument('command', nargs='?', help='Служебная команда (например, conf-dump)')

    args = parser.parse_args()

    if args.command == "conf-dump":
        print("=== Конфигурация эмулятора ===")
        print(f"VFS Path: {args.vfs or 'None'}")
        print(f"Start Script: {args.script or 'None'}")
        print("==============================")
        sys.exit(0)

    return args

def main():
    config = parse_config()

    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    app = ShellEmulatorGUI(root, vfs_path=config.vfs, start_script=config.script)
    root.mainloop()

if __name__ == "__main__":
    main()
