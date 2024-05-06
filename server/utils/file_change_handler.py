import pathlib
from collections.abc import Callable

from watchdog.events import FileSystemEventHandler

import logging


class FileChangeHandler(FileSystemEventHandler):
    """
    A class that handles file changes and notifies observers when the file is modified.
    """
    logger: logging.Logger
    file_path: pathlib.Path
    file_position: int
    observers: list[Callable[[list[str]], None]]

    def __init__(self, file_handler_logger: logging.Logger, file_path: pathlib.Path):
        super().__init__()
        self.logger = file_handler_logger
        self.file_path = file_path.absolute()
        self.file_position = self._get_initial_file_position()
        self.observers = []

    def _get_initial_file_position(self):
        """
        Opens the file and seeks to the end to find the initial file position.
        :return: The initial file position.
        """
        with open(self.file_path, 'r') as file:
            file.seek(0, 2)  # Move to the end of the file
            return file.tell()

    def register_observer(self, observer: Callable[[list[str]], None]):
        """
        Register an observer to be notified when the file is modified.
        :param observer: The observer to register.
        """
        self.observers.append(observer)

    def remove_observer(self, observer: Callable[[list[str]], None]):
        """
        Remove an observer from the list of observers.
        :param observer: The observer to remove.
        """
        self.observers.remove(observer)

    def _notify_observers(self, new_lines: list[str]):
        """
        Notify all observers that the file has been modified.
        :param new_lines: The new lines that have been added to the file.
        """
        for observer in self.observers:
            observer(new_lines)

    def on_modified(self, event):
        """
        Called when the file is modified.
        :param event: The event that triggered the call.
        """
        # Check if the modified file is the file we're interested in
        if not event.is_directory and pathlib.Path(event.src_path).absolute() == self.file_path:
            self.logger.debug(f"File {self.file_path.name} has been modified. Reading new lines...")
            with open(self.file_path, 'r') as file:
                # Seek to the last known position
                file.seek(self.file_position)
                # Read new lines and update the file position
                new_lines = file.readlines()
                self.file_position = file.tell()

                # Notify observers
                self._notify_observers(new_lines)

    def read_file(self) -> str:
        """
        Reads the observed file and returns its content.
        :return: The content of the file.
        """
        with open(self.file_path, 'r') as file:
            return file.read()
