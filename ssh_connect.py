import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "ssh_config.json"
DEFAULT_SSH_DIR = Path(os.path.expanduser("~")) / ".ssh"


@dataclass
class SSHSettings:
    host: str
    user: str
    port: int = 22
    key_path: Optional[str] = None
    local_port: int = 0
    remote_host: str = "127.0.0.1"
    remote_port: int = 0


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("ssh_connect")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    fmt = "[%(asctime)s] [%(levelname)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


LOG = setup_logging()


def load_settings(path: Path = CONFIG_PATH) -> SSHSettings:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        return SSHSettings(
            host=data["host"],
            user=data["user"],
            port=int(data.get("port", 22)),
            key_path=data.get("key_path"),
            local_port=int(data["local_port"]),
            remote_host=data.get("remote_host", "127.0.0.1"),
            remote_port=int(data["remote_port"]),
        )
    except KeyError as exc:
        raise KeyError(f"Missing required ssh_config.json field: {exc}") from exc


def resolve_key_path(settings: SSHSettings) -> Path:
    if settings.key_path:
        key = Path(settings.key_path)
        if not key.is_absolute():
            key = DEFAULT_SSH_DIR / key
    else:
        key = DEFAULT_SSH_DIR / "id_rsa"
    return key


def ensure_key_exists_and_fix(key_path: Path) -> None:
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found at: {key_path}")

    try:
        if os.name == "nt":
            os.chmod(key_path, 0o600)
        else:
            os.chmod(key_path, 0o600)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("Could not normalize key permissions: %s", exc)

    try:
        content = key_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read key file: {exc}") from exc

    if "PRIVATE KEY" not in content:
        LOG.warning("Key file does not look like a standard private key (no 'PRIVATE KEY' header)")
        return

    normalized = "\n".join(line.rstrip() for line in content.replace("\r", "").split("\n")) + "\n"
    if normalized != content:
        try:
            key_path.write_text(normalized, encoding="utf-8")
            LOG.info("Normalized key file line endings and trailing spaces")
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Failed to write normalized key file: %s", exc)


def build_ssh_tunnel_command(settings: SSHSettings, key_path: Path) -> list[str]:
    forward = f"{settings.local_port}:{settings.remote_host}:{settings.remote_port}"
    cmd = [
        "ssh",
        "-i",
        str(key_path),
        "-p",
        str(settings.port),
        "-o",
        "StrictHostKeyChecking=no",
        "-N",
        "-L",
        forward,
        f"{settings.user}@{settings.host}",
    ]
    return cmd


def start_tunnel(settings: SSHSettings) -> int:
    key_path = resolve_key_path(settings)
    ensure_key_exists_and_fix(key_path)

    cmd = build_ssh_tunnel_command(settings, key_path)
    LOG.info(
        "Starting SSH tunnel: local %s -> %s:%s (user=%s host=%s)",
        settings.local_port,
        settings.remote_host,
        settings.remote_port,
        settings.user,
        settings.host,
    )

    try:
        proc = subprocess.Popen(cmd)  # noqa: S603
    except FileNotFoundError:
        LOG.error("'ssh' command not found. Install OpenSSH client and ensure it is in PATH.")
        return 127
    except Exception as exc:  # noqa: BLE001
        LOG.error("Failed to start ssh process: %s", exc)
        return 1

    LOG.info("SSH tunnel started (PID=%s). Press Ctrl+C to stop.", proc.pid)

    try:
        proc.wait()
        return proc.returncode or 0
    except KeyboardInterrupt:
        LOG.info("Interrupted by user, terminating ssh tunnel...")
        proc.terminate()
        return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])

    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(
            "Usage: python ssh_connect.py\n"
            "\n"
            "Reads connection settings from ssh_config.json in the project root and\n"
            "starts an SSH tunnel from local_port to remote_host:remote_port.\n"
        )
        return 0

    try:
        settings = load_settings()
    except FileNotFoundError as exc:
        LOG.error("%s", exc)
        return 1
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        LOG.error("Invalid ssh_config.json: %s", exc)
        return 1

    return start_tunnel(settings)


if __name__ == "__main__":
    raise SystemExit(main())
