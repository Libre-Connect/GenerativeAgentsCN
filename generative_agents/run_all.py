import os
import sys
import time
import subprocess
import urllib.request
import urllib.error


def wait_for_url(url: str, timeout_seconds: int = 30, interval_seconds: float = 0.5) -> bool:
    """Wait until the given URL responds with any content, up to timeout.
    Returns True if reachable, False otherwise.
    """
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status >= 200 and resp.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(interval_seconds)
    return False


def start_process(script_path: str, env: dict = None) -> subprocess.Popen:
    """Start a Python script file in a new process using the current interpreter."""
    python = sys.executable
    cmd = [python, "-u", script_path]
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    # Unbuffered output to see logs live
    process_env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(cmd, env=process_env)


def main():
    # 1) 启动服务（web_server，端口 5000）
    print("[run_all] Starting web_server (port 5000)...")
    base_dir = os.path.dirname(__file__)
    web_proc = start_process(os.path.join(base_dir, "web_server.py"))

    # 2) 等待服务可用
    service_ready = wait_for_url("http://127.0.0.1:5000/")
    if not service_ready:
        print("[run_all] Warning: web_server did not become ready in time.")
    else:
        print("[run_all] web_server is up.")

    # 3) 启动回放（replay，端口 8000）
    print("[run_all] Starting replay (port 8000)...")
    replay_proc = start_process(os.path.join(base_dir, "replay.py"))

    print("[run_all] Both processes started.")
    print("[run_all] Open service: http://127.0.0.1:5000/")
    print("[run_all] Open replay:  http://127.0.0.1:8000/?name=<your-data>&zoom=0.3")

    try:
        # Keep the parent process alive while children run
        while True:
            time.sleep(1)
            # Optionally check they are still alive
            if web_proc.poll() is not None:
                print("[run_all] web_server exited with code", web_proc.returncode)
                break
            if replay_proc.poll() is not None:
                print("[run_all] replay exited with code", replay_proc.returncode)
                break
    except KeyboardInterrupt:
        print("[run_all] Received KeyboardInterrupt, terminating children...")
    finally:
        # Attempt to terminate child procs
        for proc in (web_proc, replay_proc):
            try:
                if proc and proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()