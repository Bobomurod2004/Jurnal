import os

from prometheus_client import multiprocess


def child_exit(server, worker):
    multiprocess_dir = (os.getenv("PROMETHEUS_MULTIPROC_DIR") or "").strip()
    if not multiprocess_dir:
        return
    multiprocess.mark_process_dead(worker.pid)
