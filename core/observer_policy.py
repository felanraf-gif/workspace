"""Central observer and R1 policy: broad reads, explicitly scoped controlled writes."""

import os
import re
import shlex
import subprocess
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import inspect
import stat
import sys


@dataclass(frozen=True)
class RepoAuthorization:
    root: str | None
    identity: tuple | None = None

    @classmethod
    def from_startup(cls, value):
        # Only the launch environment is authority; never project data or .env.
        try:
            if not value or not os.path.isabs(value):
                return cls(None)
            root = Path(value).resolve(strict=True)
            if not root.is_dir() or not (root / '.git').exists():
                return cls(None)
            info = root.stat()
            return cls(str(root), (info.st_dev, info.st_ino))
        except (OSError, ValueError, RuntimeError):
            return cls(None)


_AUTHORIZATION = RepoAuthorization.from_startup(os.environ.get('AUTHORIZED_REPO'))
# Analysis must not write Python caches into observed repositories.
sys.dont_write_bytecode = True


def authorized_repo():
    return _AUTHORIZATION.root


def assert_write_path(path):
    """Validate scope without creating parents or following an escaping link."""
    root = _AUTHORIZATION.root
    if root is None:
        raise PermissionError('R1: no startup AUTHORIZED_REPO')
    root_info = os.stat(root, follow_symlinks=False)
    if (root_info.st_dev, root_info.st_ino) != _AUTHORIZATION.identity:
        raise PermissionError('R1: authorized root was replaced')
    target = Path(path).resolve()
    if os.path.commonpath([root, str(target)]) != root:
        raise PermissionError('R1: path outside AUTHORIZED_REPO')
    relative = target.relative_to(root)
    # A nested repository is separate authority, even when lexically inside A.
    current = Path(root)
    for part in relative.parts:
        if part == '.git':
            raise PermissionError('R1: Git metadata is not a controlled write target')
        current /= part
        if current.is_dir() and (current / '.git').exists():
            raise PermissionError('R1: nested repository is not authorized')
    if target.exists():
        info = target.stat()
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise PermissionError('R1: special file denied')
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise PermissionError('R1: hard-linked write target denied')
    return str(target)


def writable(path):
    try:
        assert_write_path(path)
        return not observer_mode()
    except (OSError, ValueError, RuntimeError, TypeError):
        return False


@contextmanager
def _parent_fd(path, create=False):
    target = assert_write_path(path)
    parts = Path(target).relative_to(_AUTHORIZATION.root).parts
    if not parts:
        raise PermissionError('R1: cannot mutate repository root')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(_AUTHORIZATION.root, flags)
    try:
        info = os.fstat(fd)
        if (info.st_dev, info.st_ino) != _AUTHORIZATION.identity:
            raise PermissionError('R1: authorized root was replaced')
        for part in parts[:-1]:
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, dir_fd=fd)
                child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd, parts[-1]
    finally:
        os.close(fd)


def scoped_open(path, mode='w', *args, **kwargs):
    """Open a regular file without symlink-following or truncation before validation."""
    if observer_mode() or mode not in {'w', 'wb', 'a', 'ab', 'x', 'xb', 'r+', 'w+', 'a+'}:
        raise PermissionError('R1: unsupported write mode')
    if kwargs.get('opener') is not None or kwargs.get('closefd') is False:
        raise PermissionError('R1: custom file opener denied')
    with _parent_fd(path, create=mode[0] in 'wax') as (parent, name):
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
        if mode[0] in 'wax':
            flags |= os.O_CREAT
        if mode[0] == 'x':
            flags |= os.O_EXCL
        if mode[0] == 'a':
            flags |= os.O_APPEND
        fd = os.open(name, flags, 0o666, dir_fd=parent)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise PermissionError('R1: non-regular or hard-linked file')
            if mode[0] == 'w':
                os.ftruncate(fd, 0)
            return os.fdopen(fd, mode, *args, **kwargs)
        except BaseException:
            os.close(fd)
            raise


def scoped_remove(path):
    if observer_mode():
        raise PermissionError('Observer forbids removal')
    with _parent_fd(path) as (parent, name):
        os.unlink(name, dir_fd=parent)


def scoped_makedirs(path, exist_ok=False):
    if observer_mode():
        raise PermissionError('Observer forbids directories')
    target = assert_write_path(path)
    if target == authorized_repo():
        if not exist_ok:
            raise FileExistsError(target)
        return
    with _parent_fd(target, create=True) as (parent, name):
        try:
            os.mkdir(name, dir_fd=parent)
        except FileExistsError:
            if not exist_ok:
                raise
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(fd)


def observer_mode():
    # Fail closed: missing configuration must never enable writes implicitly.
    return os.getenv("OBSERVER_MODE", "true").strip().lower() != "false"


observer_enabled = observer_mode


class BlockedResult(dict):
    """A blocked result cannot accidentally pass a legacy boolean success check."""

    def __bool__(self):
        return False


def blocked(action, **details):
    reason = "observer_mode" if observer_mode() else "r1_scope"
    print(f"[{'OBSERVER' if observer_mode() else 'R1'}] BLOCKED: {action}")
    return BlockedResult(details, success=False, status="blocked", blocked=True,
                         action=action, reason=reason,
                         error=f"Operation blocked by {reason}")


def mutation(action, *, controlled=False, paths=None, read_only=None):
    """One fail-closed gate; only explicitly controlled implementations may write."""
    def decorate(function):
        signature = inspect.signature(function)
        @wraps(function)
        def guarded(*args, **kwargs):
            if observer_mode():
                return blocked(action)
            values = signature.bind(*args, **kwargs).arguments
            if read_only and read_only(values):
                return function(*args, **kwargs)
            if not controlled or not authorized_repo():
                return blocked(action)
            try:
                for path in paths(values) if paths else ():
                    assert_write_path(path)
            except (OSError, ValueError, TypeError, RuntimeError) as exc:
                return blocked(action, detail=str(exc))
            return function(*args, **kwargs)
        return guarded
    return decorate


READ_TOOLS = frozenset({"file_read", "file_exists", "file_list", "grep", "find",
                        "git_status", "git_log", "git_diff", "git_branch",
                        "git_current_branch", "git_is_repo"})


def tool_allowed(name, args=None):
    if name in READ_TOOLS:
        return True
    return (not observer_mode() and name in {"file_write", "file_edit"}
            and isinstance(args, dict) and writable(args.get("path")))


def safe_git_args(command):
    """Accept only the finite read operations exposed by GitTools, never arbitrary flags."""
    try:
        parts = shlex.split(command) if isinstance(command, str) else list(command)
    except (TypeError, ValueError):
        return None
    allowed = parts in (["status"], ["status", "-s"], ["status", "--porcelain"],
                        ["branch", "-a"], ["branch", "--show-current"],
                        ["rev-parse", "--git-dir"], ["diff"], ["diff", "--cached"])
    if (len(parts) in (2, 3) and parts[0] == "log"
            and isinstance(parts[1], str) and re.fullmatch(r"-[1-9][0-9]{0,4}", parts[1])
            and (len(parts) == 2 or parts[2] == "--oneline")):
        allowed = True
    if not allowed:
        return None
    if parts[0] == "status":
        parts = [parts[0], "--ignore-submodules=all", *parts[1:]]
    elif parts[0] == "diff":
        parts = [parts[0], "--ignore-submodules=all", "--no-ext-diff",
                 "--no-textconv", *parts[1:]]
    elif parts[0] == "log":
        # Repository config may set format.pretty to a signature placeholder
        # such as %G?, which executes the configured signature verifier even
        # when log.showSignature=false. Always select a trusted format.
        log_format = "oneline" if "--oneline" in parts else "medium"
        parts = [part for part in parts if part != "--oneline"]
        parts = [parts[0], "--no-show-signature", f"--format={log_format}",
                 *parts[1:]]
    return ["git", "--no-optional-locks", "--no-pager", "-c", "core.fsmonitor=false",
            "-c", "core.hooksPath=/dev/null", "-c", "log.showSignature=false",
            "-c", "status.submoduleSummary=false", "-c", "submodule.recurse=false",
            "-c", "diff.ignoreSubmodules=all", *parts]


def git_filter_overrides(cwd):
    """Status/diff may execute clean filters: disable every configured driver.

    Querying config does not execute helpers. If config cannot be classified,
    refuse the subsequent Git command instead of running it unprotected.
    """
    result = subprocess.run(
        ["git", "config", "--null", "--name-only", "--get-regexp", r"^filter\..*\.(clean|smudge|process|required)$"],
        cwd=cwd, capture_output=True, text=True, timeout=3,
    )
    if result.returncode not in (0, 1):
        raise PermissionError("Observer cannot safely inspect Git filter configuration")
    names = {key.rsplit(".", 1)[0] for key in result.stdout.split("\0") if key}
    overrides = []
    for name in sorted(names):
        for field in ("clean", "smudge", "process"):
            overrides += ["-c", f"{name}.{field}="]
        overrides += ["-c", f"{name}.required=false"]
    return overrides
