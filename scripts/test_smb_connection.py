#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_KEYS = [
    "RECIPE_TRACE_SMB_HOST",
    "RECIPE_TRACE_SMB_SHARE",
    "RECIPE_TRACE_SMB_USER",
    "RECIPE_TRACE_SMB_PASSWORD",
    "RECIPE_TRACE_SMB_MACHINE_FOLDER",
]


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        raise FileNotFoundError(f"找不到環境檔案: {env_path}")

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if "#" in value:
            value = value.split("#", 1)[0].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, shell=False)


def is_host_reachable(host: str) -> bool:
    result = run_command(["ping", "-n", "1", host])
    return result.returncode == 0


def classify_mount_error(message: str, host_reachable: bool) -> tuple[str, int]:
    lower = message.lower()
    auth_signals = [
        "system error 5",
        "system error 86",
        "access is denied",
        "logon failure",
        "password is not correct",
        "使用者名稱或密碼不正確",
        "拒絕存取",
    ]
    share_signals = [
        "system error 67",
        "network name cannot be found",
        "找不到網路名稱",
        "共享",
    ]
    network_signals = [
        "system error 53",
        "system error 64",
        "system error 1219",
        "network path was not found",
        "網路路徑找不到",
        "無法連線",
    ]

    if any(token in lower for token in auth_signals):
        return ("認證失敗：請確認 SMB 帳號或密碼是否正確。", 3)
    if any(token in lower for token in share_signals):
        return ("共享路徑不存在：請確認 SMB share 名稱是否正確。", 4)
    if not host_reachable or any(token in lower for token in network_signals):
        return ("網路連線失敗：無法連線到 SMB 伺服器。", 2)
    return ("連線失敗：請檢查網路、帳密與共享設定。", 1)


def cleanup_mount(target_unc: str) -> None:
    run_command(["net", "use", target_unc, "/delete", "/y"])


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / "web" / ".env"
    load_env_file(env_path)

    missing = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    if missing:
        print(f"缺少必要環境變數: {', '.join(missing)}")
        return 1

    host = os.environ["RECIPE_TRACE_SMB_HOST"]
    share = os.environ["RECIPE_TRACE_SMB_SHARE"]
    user = os.environ["RECIPE_TRACE_SMB_USER"]
    password = os.environ["RECIPE_TRACE_SMB_PASSWORD"]
    machine_folder = os.environ["RECIPE_TRACE_SMB_MACHINE_FOLDER"]

    target_unc = f"\\\\{host}\\{share}"
    machine_unc = f"{target_unc}\\{machine_folder}"

    host_reachable = is_host_reachable(host)
    if not host_reachable:
        print(f"網路連線失敗：無法 ping 到 SMB 主機 {host}")
        return 2

    # 清掉現有連線避免使用到快取憑證。
    cleanup_mount(target_unc)

    mount_result = run_command(
        ["net", "use", target_unc, password, f"/user:{user}", "/persistent:no"]
    )
    mount_output = (mount_result.stdout or "") + (mount_result.stderr or "")
    if mount_result.returncode != 0:
        message, code = classify_mount_error(mount_output, host_reachable)
        print(message)
        print("net use 輸出:")
        print(mount_output.strip())
        cleanup_mount(target_unc)
        return code

    try:
        machine_path = Path(machine_unc)
        if not machine_path.exists():
            print(f"共享路徑不存在：找不到資料夾 {machine_unc}")
            return 4

        eqpid_dirs = sorted(p.name for p in machine_path.iterdir() if p.is_dir())
        print("SMB 連線成功。")
        print(f"目標資料夾: {machine_unc}")
        if eqpid_dirs:
            print("eqpid 子目錄清單:")
            for item in eqpid_dirs:
                print(f"- {item}")
        else:
            print("未找到任何 eqpid 子目錄。")
        return 0
    finally:
        cleanup_mount(target_unc)


if __name__ == "__main__":
    sys.exit(main())
