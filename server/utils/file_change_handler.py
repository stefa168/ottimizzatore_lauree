import pathlib

from watchdog.events import FileSystemEventHandler

import logging


class FileChangeHandler(FileSystemEventHandler):
    logger: logging.Logger
    file_path: pathlib.Path
    file_position: int

    def __init__(self, file_handler_logger: logging.Logger, file_path: pathlib.Path):
        super().__init__()
        self.logger = file_handler_logger
        self.file_path = file_path.absolute()
        self.file_position = self.get_initial_file_position()

    def get_initial_file_position(self):
        """Open the file and seek to the end to find the initial file position."""
        with open(self.file_path, 'r') as file:
            file.seek(0, 2)  # Move to the end of the file
            return file.tell()

    def on_modified(self, event):
        # Check if the modified file is the file we're interested in
        if not event.is_directory and pathlib.Path(event.src_path).absolute() == self.file_path:
            self.logger.debug(f"File {self.file_path.name} has been modified. Reading new lines...")
            with open(self.file_path, 'r') as file:
                # Seek to the last known position
                file.seek(self.file_position)
                # Read new lines and update the file position
                new_lines = file.readlines()
                self.file_position = file.tell()

                # Log the new lines
                for line in new_lines:
                    self.logger.info(line.strip())
