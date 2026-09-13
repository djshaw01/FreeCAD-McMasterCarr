"""GUI-thread polling watcher for newly completed STEP downloads."""

import os
from pathlib import Path

from PySide import QtCore

from .importer import import_step


def system_download_directory() -> Path | None:
    """Return existing system Downloads directory reported by Qt."""
    try:
        location = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DownloadLocation)
    except (AttributeError, TypeError):
        return None
    if not location:
        return None
    directory = Path(location).expanduser().resolve()
    return directory if directory.is_dir() else None


def is_step_file(path: Path) -> bool:
    if path.suffix.lower() not in (".step", ".stp"):
        return False
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return False
        with path.open("rb") as stream:
            header = stream.read(4096).lstrip()
    except OSError:
        return False
    return header.startswith(b"ISO-10303-21;")


def _destination_for(path: Path, directory: Path, attempt: int) -> Path:
    if attempt == 0:
        return directory / path.name
    return directory / f"{path.stem}-{attempt}{path.suffix}"


def _relocate_exclusive(source: Path, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for attempt in range(1000):
        destination = _destination_for(source, directory, attempt)
        try:
            with destination.open("xb") as target:
                with source.open("rb") as source_stream:
                    import shutil
                    shutil.copyfileobj(source_stream, target)
                target.flush()
                os.fsync(target.fileno())
        except FileExistsError:
            continue
        except Exception:
            if source.exists():
                try:
                    destination.unlink()
                except OSError:
                    pass
            raise
        try:
            source.unlink()
        except Exception:
            if source.exists():
                try:
                    destination.unlink()
                except OSError:
                    pass
            raise
        return destination
    raise OSError("could not reserve a unique destination filename")


class DownloadWatchSession(QtCore.QObject):
    finished = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, directory: Path, document_name: str, parent=None, system_directory=None):
        super().__init__(parent)
        self.directory = Path(directory).expanduser().resolve()
        if system_directory is not None:
            system = Path(system_directory).expanduser().resolve()
        else:
            system = system_download_directory()
        self.directories = (self.directory,) if system is None or system == self.directory else (self.directory, system)
        self.document_name = document_name
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._scan)
        self._initial = {}
        self._candidates = {}
        self._done = False

    def start(self) -> None:
        try:
            self._initial = self._snapshot()
        except OSError:
            self._finish_error(f"Download folder is unavailable: {self.directory}")
            return
        self.timer.start()

    def cancel(self) -> None:
        if self._done:
            return
        self.timer.stop()
        self._done = True
        self.finished.emit()

    def _snapshot(self):
        result = {}
        if not self.directory.is_dir():
            raise OSError
        for directory in self.directories:
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                if path.is_file() and path.suffix.lower() in (".step", ".stp"):
                    try:
                        stat = path.stat()
                    except OSError:
                        continue
                    result[path.resolve()] = (stat.st_size, stat.st_mtime_ns)
        return result

    def _scan(self) -> None:
        if self._done:
            return
        try:
            current = self._snapshot()
        except OSError:
            self._finish_error(f"Download folder is unavailable: {self.directory}")
            return
        ready = []
        for path, signature in current.items():
            if path in self._initial and self._initial[path] == signature:
                continue
            state = self._candidates.get(path)
            if state is None or state[0] != signature:
                self._candidates[path] = (signature, 1, False)
                continue
            stable = state[1] + 1
            invalid = state[2]
            if stable < 2:
                self._candidates[path] = (signature, stable, invalid)
                continue
            if invalid:
                continue
            if is_step_file(path):
                ready.append(path)
            else:
                self._candidates[path] = (signature, stable, True)
        if ready:
            path = min(ready, key=lambda item: (current[item][1], str(item)))
            self.timer.stop()
            self._done = True
            try:
                if path.parent != self.directory:
                    path = _relocate_exclusive(path, self.directory)
                import_step(path, self.document_name)
            except RuntimeError as exc:
                self.error.emit(str(exc))
            except OSError as exc:
                self.error.emit(f"Could not move STEP file: {exc}")
            else:
                self.error.emit(f"STEP file imported: {path}")
            self.finished.emit()

    def _finish_error(self, message: str) -> None:
        self.timer.stop()
        self._done = True
        self.error.emit(message)
        self.finished.emit()
