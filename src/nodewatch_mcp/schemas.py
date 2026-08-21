import datetime

from pydantic import BaseModel, Field


class CpuMetrics(BaseModel):
    """CPU metrics including usage and core counts."""

    logical_cores: int = Field(..., description="Number of logical CPU cores.")
    physical_cores: int = Field(..., description="Number of physical CPU cores.")
    usage_per_core: list[float] = Field(
        ..., description="CPU usage percentage for each core."
    )
    total_usage: float = Field(..., description="Overall CPU usage percentage.")


class MemoryUsage(BaseModel):
    """Detailed memory usage statistics."""

    total: int = Field(..., description="Total memory in bytes.")
    available: int = Field(..., description="Available memory in bytes.")
    used: int = Field(..., description="Used memory in bytes.")
    free: int = Field(..., description="Free memory in bytes.")
    percent: float = Field(..., description="Memory usage percentage.")


class SwapMemoryUsage(BaseModel):
    """Detailed swap memory usage statistics."""

    total: int = Field(..., description="Total swap memory in bytes.")
    used: int = Field(..., description="Used swap memory in bytes.")
    free: int = Field(..., description="Free swap memory in bytes.")
    percent: float = Field(..., description="Swap memory usage percentage.")
    sin: int = Field(..., description="Number of bytes swapped in.")
    sout: int = Field(..., description="Number of bytes swapped out.")


class MemoryMetrics(BaseModel):
    """RAM and Swap memory metrics."""

    ram: MemoryUsage
    swap: SwapMemoryUsage


class DiskUsage(BaseModel):
    """Disk usage statistics for a partition."""

    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


class DiskMetrics(BaseModel):
    """A list of disk usage statistics for all partitions."""

    partitions: list[DiskUsage]


class NetworkInterfaceMetrics(BaseModel):
    """Network I/O statistics for a single interface."""

    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


class NetworkMetrics(BaseModel):
    """A dictionary of network metrics for all interfaces."""

    interfaces: dict[str, NetworkInterfaceMetrics]


class Process(BaseModel):
    """Details of a running process."""

    pid: int
    name: str = "unknown"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    username: str | None = None
    status: str = "unknown"


class TopProcesses(BaseModel):
    """A list of the top resource-consuming processes."""

    processes: list[Process] = Field(default_factory=list)


class SystemOverview(BaseModel):
    """A high-level overview of the system."""

    hostname: str
    os: str
    uptime: str
    boot_time: datetime.datetime


class LogFiles(BaseModel):
    """A list of log filenames."""

    files: list[str] = Field(default_factory=list)


class LogRecords(BaseModel):
    """A list of log records."""

    records: list[str] = Field(default_factory=list)


class OpenPort(BaseModel):
    """Details of an open port and the process using it."""

    port: int
    protocol: str
    status: str
    pid: int | None = None
    process_name: str | None = None
