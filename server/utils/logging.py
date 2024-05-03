import sys
import logging


def is_valid_log_level(level_name):
    return level_name in logging.getLevelNamesMapping().keys()


def redirect_stdout(new_target):
    class RedirectStdout:
        def __enter__(self):
            self.old_stdout = sys.stdout
            sys.stdout = new_target
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            sys.stdout = self.old_stdout

    return RedirectStdout()


def redirect_stderr(new_target):
    class RedirectStderr:
        def __enter__(self):
            self.old_stderr = sys.stderr
            sys.stderr = new_target
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            sys.stderr = self.old_stderr

    return RedirectStderr()
