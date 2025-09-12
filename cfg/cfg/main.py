#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shlex
import getpass
import socket
import tkinter as tk
from tkinter import ttk

APP_NAME = "Emylyatorka"

class ShellEmulatorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.cwd = os.getcwd()

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.9)
        x_offset = int(screen_width * 0.05)
        y_offset = int(screen_height * 0.05)
        self.root.geometry(f"{width}x{height}+{x_offset}+{y_offset}")
        self.root.title(f"{APP_NAME} - [{self.username}@{self.hostname}]")

        container = ttk.Frame(root, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        self.output = tk.Text(container, wrap=tk.WORD, state=tk.NORMAL)
        self.output.configure(font=("Consolas", 11))
        self.output.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(container, textvariable=self.entry_var)
        self.entry.pack(fill=tk.X, side=tk.BOTTOM)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Up>", self.on_history_up)
        self.entry.bind("<Down>", self.on_history_down)

        self.history = []
        self.history_index = None

        self._print_welcome()
        self._print_prompt()
        self.entry.focus_set()

    def _prompt_str(self) -> str:
        short_cwd = os.path.basename(self.cwd) or "/"
        return f"[{self.username}@{self.hostname} {short_cwd}]$ "

    def _print_prompt(self):
        self._append(self._prompt_str())

    def _append(self, text: str, end: str = "\n"):
        self.output.insert(tk.END, text + end)
        self.output.see(tk.END)

    def _append_inline(self, text: str):
        self.output.insert(tk.END, text)
        self.output.see(tk.END)

    def _print_welcome(self):
        lines = [
            f"{APP_NAME} — прототип (Этап 1)."
        ]
        for line in lines:
            self._append(line)

    def on_enter(self, event=None):
        raw = self.entry_var.get()
        self.entry_var.set("")

        self._append_inline(self._prompt_str())
        self._append(raw)

        if not raw.strip():
            self._print_prompt()
            return

        if not self.history or (self.history and self.history[-1] != raw):
            self.history.append(raw)
        self.history_index = None

        self.execute_line(raw)

    def on_history_up(self, event=None):
        if not self.history:
            return
        if self.history_index is None:
            self.history_index = len(self.history) - 1
        else:
            self.history_index = max(0, self.history_index - 1)
        self.entry_var.set(self.history[self.history_index])
        self.entry.icursor(tk.END)

    def on_history_down(self, event=None):
        if self.history_index is None:
            return
        self.history_index = min(len(self.history) - 1, self.history_index + 1)
        self.entry_var.set(self.history[self.history_index])
        self.entry.icursor(tk.END)
        if self.history_index == len(self.history) - 1:
            self.history_index = None

    def expand_env(self, line: str) -> str:
        expanded = os.path.expandvars(line)
        expanded = os.path.expanduser(expanded)
        return expanded

    def parse_line(self, line: str):
        expanded = self.expand_env(line)
        try:
            parts = shlex.split(expanded, posix=True)
        except ValueError as e:
            raise ParseError(str(e))
        return parts

    def execute_line(self, line: str):
        try:
            parts = self.parse_line(line)
        except ParseError as e:
            self._append(f"Ошибка парсинга: {e}")
            self._print_prompt()
            return

        if not parts:
            self._print_prompt()
            return

        cmd, *args = parts

        if cmd == "exit":
            self._append("Завершение работы…")
            self.root.after(50, self.root.destroy)
            return
        elif cmd == "ls":
            self.cmd_ls(args)
        elif cmd == "cd":
            self.cmd_cd(args)
        else:
            self._append(f"Ошибка: неизвестная команда: {cmd}")

        self._print_prompt()

    def cmd_ls(self, args):
        if args and "--help" in args:
            self._append("Использование: ls [АРГУМЕНТЫ]  # заглушка, выводит имя и аргументы")
            return
        self._append(f"ls :: args={args}")

    def cmd_cd(self, args):
        if len(args) > 1:
            self._append("Ошибка: неверные аргументы для cd. Ожидалось 0 или 1 аргумент.")
            return
        self._append(f"cd :: args={args}")
        if len(args) == 1:
            target = args[0]
            if os.path.isdir(target):
                self.cwd = os.path.abspath(target)
            else:
                self._append(f"Предупреждение: директория '{target}' не найдена (эмуляция). cwd не изменён.")

class ParseError(Exception):
    pass

def main():
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

    app = ShellEmulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
