"""Runtime persistence respecting observer mode and R1; never replaces global I/O.

Existing files remain readable. Out-of-scope runtime writes are reported and kept
in RAM, so missing authority does not interrupt analysis. In-scope writes use
the same guarded file opening as execution tools. This adapter is
for agent-owned state, never for execution tools or patch targets.
"""
import builtins
import io
import os as _os
from core.observer_policy import (observer_mode, blocked, writable, scoped_open,
                                  scoped_makedirs, scoped_remove)

_files = {}
_directories = set()


def _key(path):
    return _os.path.abspath(_os.fspath(path))


class _Buffer(io.StringIO):
    def __init__(self, path, value):
        super().__init__(value)
        self.path = path

    def close(self):
        if not self.closed:
            _files[self.path] = self.getvalue()
        super().close()


def open(file, mode='r', *args, **kwargs):
    key = _key(file)
    writing = any(flag in mode for flag in 'wax+')
    if writing and writable(file):
        return scoped_open(file, mode, *args, **kwargs)
    if writing:
        if 'b' in mode:
            raise PermissionError('Observer runtime supports text state only')
        blocked('runtime.persist', path=key, storage='process-memory')
        value = ''
        if 'a' in mode or '+' in mode:
            if key in _files:
                value = _files[key]
            elif _os.path.isfile(key):
                with builtins.open(key, encoding=kwargs.get('encoding') or 'utf-8') as source:
                    value = source.read()
        stream = _Buffer(key, value)
        if 'a' in mode:
            stream.seek(0, 2)
        return stream
    if key in _files:
        return io.BytesIO(_files[key].encode()) if 'b' in mode else io.StringIO(_files[key])
    return builtins.open(file, mode, *args, **kwargs)


class _Path:
    def exists(self, path):
        return (_key(path) in _files or _key(path) in _directories) or _os.path.exists(path)

    def __getattr__(self, name):
        return getattr(_os.path, name)


class _OS:
    path = _Path()

    def makedirs(self, path, *args, **kwargs):
        if not writable(path):
            _directories.add(_key(path))
            return
        return scoped_makedirs(path, exist_ok=kwargs.get("exist_ok", False))

    def remove(self, path):
        if not writable(path):
            return blocked('runtime.remove', path=str(path))
        return scoped_remove(path)

    def listdir(self, path):
        if not _os.path.isdir(path) and _key(path) in _directories:
            return []
        return _os.listdir(path)

    def __getattr__(self, name):
        # Unknown OS operations fail closed; this facade is only for state I/O.
        readonly = {"walk", "stat", "lstat", "getcwd", "getenv", "environ",
                    "fspath", "PathLike", "sep", "name", "scandir", "access"}
        if name not in readonly:
            def denied(*args, **kwargs):
                return blocked("runtime.os." + name)
            return denied
        return getattr(_os, name)


os = _OS()
