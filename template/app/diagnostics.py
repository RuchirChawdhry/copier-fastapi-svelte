import time
from pathlib import Path

import psutil
from pydantic import BaseModel


class Diagnostics(BaseModel):
    cpu_percent: float
    logical_cpus: int | None
    memory_used_bytes: int
    memory_total_bytes: int
    disk_used_bytes: int
    disk_total_bytes: int
    process_rss_bytes: int
    uptime_seconds: int


def collect_diagnostics(path: Path) -> Diagnostics:
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(path.resolve()))
    return Diagnostics(
        cpu_percent=psutil.cpu_percent(interval=0.1),
        logical_cpus=psutil.cpu_count(),
        memory_used_bytes=memory.total - memory.available,
        memory_total_bytes=memory.total,
        disk_used_bytes=disk.used,
        disk_total_bytes=disk.total,
        process_rss_bytes=psutil.Process().memory_info().rss,
        uptime_seconds=int(time.time() - psutil.boot_time()),
    )

