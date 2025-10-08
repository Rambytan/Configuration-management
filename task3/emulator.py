# emulator.py
import os
import shlex
import getpass
import socket
import tkinter as tk
from tkinter import ttk
import zipfile
import base64

APP_NAME = "Эмулятор"


class VFS:
    def __init__(self):
        self.files = {}
        self.dirs = {}
        self.current_vfs_path = None

    def load_from_zip(self, zip_path):
        """Загружает VFS из ZIP-архива"""
        try:
            if not os.path.exists(zip_path):
                raise FileNotFoundError(f"VFS файл не найден: {zip_path}")

            self.files = {}
            self.dirs = {'/': []}

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.is_dir():
                        # Обрабатываем директории
                        path = '/' + file_info.filename.rstrip('/')
                        if path not in self.dirs:
                            self.dirs[path] = []
                    else:
                        # Обрабатываем файлы - ВСЕ данные храним в base64
                        with zip_ref.open(file_info.filename) as f:
                            content = f.read()
                            # Все файлы сохраняем в base64 для единообразия
                            content_b64 = base64.b64encode(content).decode('utf-8')
                            self.files['/' + file_info.filename] = {
                                'content': content_b64,
                                'is_binary': True,
                                'original_size': len(content),
                                'name': file_info.filename
                            }

                        # Добавляем файл в структуру директорий
                        dir_path = os.path.dirname('/' + file_info.filename)
                        if dir_path == '':
                            dir_path = '/'

                        if dir_path not in self.dirs:
                            self.dirs[dir_path] = []

                        filename = os.path.basename(file_info.filename)
                        if filename not in self.dirs[dir_path]:
                            self.dirs[dir_path].append(filename)

            self.current_vfs_path = zip_path
            return True

        except zipfile.BadZipFile:
            raise ValueError(f"Неверный формат ZIP-архива: {zip_path}")
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки VFS: {e}")

    def list_directory(self, path):
        """Возвращает содержимое директории"""
        if path in self.dirs:
            return self.dirs[path]
        return []

    def file_exists(self, path):
        """Проверяет существование файла"""
        return path in self.files

    def read_file(self, path):
        """Читает содержимое файла"""
        if path in self.files:
            file_info = self.files[path]
            if file_info['is_binary']:
                # Для бинарных файлов показываем информацию и sample base64
                base64_content = file_info['content']
                sample = base64_content[:50] + "..." if len(base64_content) > 50 else base64_content
                return (f"[Бинарный файл: {file_info['name']}]\n"
                        f"Размер: {file_info['original_size']} байт\n"
                        f"Base64 (первые 50 символов): {sample}\n"
                        f"Полный base64 размер: {len(base64_content)} символов")
            else:
                return file_info['content']
        return None

    def get_file_info(self, path):
        """Возвращает информацию о файле"""
        if path in self.files:
            file_info = self.files[path]
            return {
                'size': len(file_info['content']),
                'is_binary': file_info['is_binary']
            }
        return None


class ShellEmulatorGUI:
    def __init__(self, root: tk.Tk, vfs_path=None, start_script=None):
        self.root = root
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.cwd = '/'
        self.vfs = VFS()
        self.vfs_loaded = False
        self.script_error_occurred = False

        self._init_gui()

        if vfs_path:
            try:
                self.vfs.load_from_zip(vfs_path)
                self.vfs_loaded = True
                self._append(f"VFS успешно загружена из: {vfs_path}")
            except Exception as e:
                self._append(f"Ошибка загрузки VFS: {e}")
                self.vfs_loaded = False

       ## self._print_welcome()
        self._print_prompt()
        self.entry.focus_set()

        # Запуск стартового скрипта, если указан
        if start_script and not self.script_error_occurred:
            self.run_script(start_script)

    def _init_gui(self):
        """Инициализация всех GUI элементов"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.9)
        x_offset = int(screen_width * 0.05)
        y_offset = int(screen_height * 0.05)
        self.root.geometry(f"{width}x{height}+{x_offset}+{y_offset}")
        self.root.title(f"{APP_NAME} - [{self.username}@{self.hostname}] - VFS: {self.vfs_loaded}")

        container = ttk.Frame(self.root, padding=8)
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

    def _prompt_str(self) -> str:
        short_cwd = os.path.basename(self.cwd) or "/"
        vfs_status = "VFS" if self.vfs_loaded else "NO-VFS"
        return f"[{self.username}@{self.hostname} {short_cwd}]{vfs_status}$ "

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
            f"{APP_NAME} — прототип (Этап 3 с VFS).",
            "Поддерживаемые команды: ls, cd, cat, echo, exit, vfs-info.",
            "Переменные окружения: используйте $HOME, $PATH, ${USER} и т.д.",
            "VFS команды: cat <file> - просмотр файлов VFS",
            "Примеры для демонстрации:",
            "  ls /",
            "  cd /folder",
            "  cat file.txt",
            "  echo 'Hello World'",
            "  vfs-info",
            "  unknowncmd",
            "  cd arg1 arg2  # ошибка неверных аргументов",
            "  exit",
            ""
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

        self.execute_line(raw, from_script=False)

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

    def execute_line(self, line: str, from_script=True):
        if from_script and self.script_error_occurred:
            return False

        try:
            parts = self.parse_line(line)
        except ParseError as e:
            self._append(f"Ошибка парсинга: {e}")
            if from_script:
                self.script_error_occurred = True
            self._print_prompt()
            return False

        if not parts:
            self._print_prompt()
            return True

        cmd, *args = parts

        if cmd == "exit":
            self._append("Завершение работы…")
            self.root.after(50, self.root.destroy)
            return True
        elif cmd == "ls":
            success = self.cmd_ls(args)
        elif cmd == "cd":
            success = self.cmd_cd(args)
        elif cmd == "cat":
            success = self.cmd_cat(args)
        elif cmd == "echo":
            success = self.cmd_echo(args)
        elif cmd == "vfs-info":
            success = self.cmd_vfs_info(args)
        else:
            self._append(f"Ошибка: неизвестная команда: {cmd}")
            if from_script:
                self.script_error_occurred = True
            self._print_prompt()
            return False

        self._print_prompt()
        return success

    def cmd_ls(self, args):
        if args and "--help" in args:
            self._append("Использование: ls [ПУТЬ] - список файлов и папок")
            return True

        path = self.cwd
        if args:
            path = args[0]
            if not path.startswith('/'):
                path = os.path.join(self.cwd, path).replace('\\', '/')

        if self.vfs_loaded:
            if path in self.vfs.dirs:
                items = self.vfs.list_directory(path)
                for item in sorted(items):
                    self._append(item)
            else:
                self._append(f"Ошибка: директория не найдена: {path}")
                return False
        else:
            self._append(f"ls :: path={path} (VFS не загружена)")

        return True

    def cmd_cd(self, args):
        if len(args) > 1:
            self._append("Ошибка: неверные аргументы для cd. Ожидалось 0 или 1 аргумент.")
            return False

        if self.vfs_loaded:
            if len(args) == 1:
                target = args[0]
                if target == "..":
                    # Переход на уровень выше
                    self.cwd = os.path.dirname(self.cwd) or '/'
                elif target.startswith('/'):
                    # Абсолютный путь
                    if target in self.vfs.dirs:
                        self.cwd = target
                    else:
                        self._append(f"Ошибка: директория не найдена: {target}")
                        return False
                else:
                    # Относительный путь
                    new_path = os.path.join(self.cwd, target).replace('\\', '/')
                    if new_path in self.vfs.dirs:
                        self.cwd = new_path
                    else:
                        self._append(f"Ошибка: директория не найдена: {new_path}")
                        return False
            else:
                # cd без аргументов - в корень
                self.cwd = '/'

            self._append(f"Текущая директория: {self.cwd}")
        else:
            self._append(f"cd :: args={args} (VFS не загружена)")
            if len(args) == 1:
                target = args[0]
                self.cwd = os.path.abspath(os.path.join(self.cwd, target))
            else:
                self.cwd = '/'

        return True

    def cmd_cat(self, args):
        if not args:
            self._append("Использование: cat <ФАЙЛ> - просмотр содержимого файла")
            return False

        if not self.vfs_loaded:
            self._append("Ошибка: VFS не загружена")
            return False

        filename = args[0]
        if not filename.startswith('/'):
            filename = os.path.join(self.cwd, filename).replace('\\', '/')

        if self.vfs.file_exists(filename):
            content = self.vfs.read_file(filename)
            self._append(f"Содержимое файла {filename}:")
            self._append(content)
        else:
            self._append(f"Ошибка: файл не найден: {filename}")
            return False

        return True

    def cmd_echo(self, args):
        """Команда echo - вывод текста"""
        if not args:
            self._append("")  # Просто пустая строка
            return True

        # Объединяем все аргументы в одну строку
        text = ' '.join(args)
        self._append(text)
        return True

    def cmd_vfs_info(self, args):
        if self.vfs_loaded:
            self._append("=== Информация о VFS ===")
            self._append(f"Путь к VFS: {self.vfs.current_vfs_path}")
            self._append(f"Количество файлов: {len(self.vfs.files)}")
            self._append(f"Количество директорий: {len(self.vfs.dirs)}")
            self._append(f"Текущая директория: {self.cwd}")

            # Показываем структуру VFS
            self._append("\nКорневая структура VFS:")
            root_items = self.vfs.list_directory('/')
            for item in sorted(root_items):
                self._append(f"  {item}")
        else:
            self._append("VFS не загружена")

        return True

    def run_script(self, script_path):
        """Выполняет команды из скрипта построчно с остановкой при первой ошибке"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            self._append(f"\n=== Выполнение скрипта: {script_path} ===")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    self._append_inline(self._prompt_str())
                    self._append(line)

                    success = self.execute_line(line, from_script=True)

                    if not success:
                        self._append(f"=== Выполнение скрипта прервано на строке {line_num} ===")
                        break

            if not self.script_error_occurred:
                self._append("=== Скрипт выполнен успешно ===")

        except Exception as e:
            self._append(f"Ошибка выполнения скрипта: {e}")
            self.script_error_occurred = True


class ParseError(Exception):
    pass
