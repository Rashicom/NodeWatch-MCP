import datetime

import pytest

from nodewatch_mcp.metrics import (
    get_cpu_metrics,
    get_disk_metrics,
    get_log_records,
    get_memory_metrics,
    get_network_metrics,
    get_system_overview,
    get_top_processes,
    list_log_files,
)
from nodewatch_mcp.schemas import (
    CpuMetrics,
    DiskMetrics,
    LogFiles,
    LogRecords,
    MemoryMetrics,
    NetworkMetrics,
    SystemOverview,
    TopProcesses,
)


def test_get_system_overview():
    """Tests the get_system_overview function."""
    overview = get_system_overview()
    assert isinstance(overview, SystemOverview)
    assert isinstance(overview.hostname, str) and overview.hostname
    assert isinstance(overview.os, str) and overview.os
    assert isinstance(overview.uptime, str) and overview.uptime
    assert isinstance(overview.boot_time, datetime.datetime)


def test_get_cpu_metrics():
    """Tests the get_cpu_metrics function."""
    metrics = get_cpu_metrics()
    assert isinstance(metrics, CpuMetrics)
    assert metrics.logical_cores > 0
    assert metrics.physical_cores > 0
    assert isinstance(metrics.usage_per_core, list)
    assert len(metrics.usage_per_core) == metrics.logical_cores
    assert all(isinstance(core_usage, float) for core_usage in metrics.usage_per_core)
    assert 0.0 <= metrics.total_usage <= 100.0


def test_get_memory_metrics():
    """Tests the get_memory_metrics function."""
    metrics = get_memory_metrics()
    assert isinstance(metrics, MemoryMetrics)

    # Test RAM metrics
    assert metrics.ram.total >= 0
    assert metrics.ram.available >= 0
    assert metrics.ram.used >= 0
    assert metrics.ram.free >= 0
    assert 0.0 <= metrics.ram.percent <= 100.0

    # Test Swap metrics
    assert metrics.swap.total >= 0
    assert metrics.swap.used >= 0
    assert metrics.swap.free >= 0
    assert 0.0 <= metrics.swap.percent <= 100.0


def test_get_disk_metrics():
    """Tests the get_disk_metrics function."""
    metrics = get_disk_metrics()
    assert isinstance(metrics, DiskMetrics)
    assert isinstance(metrics.partitions, list)
    if metrics.partitions:
        part = metrics.partitions[0]
        assert isinstance(part.device, str)
        assert isinstance(part.mountpoint, str)
        assert 0.0 <= part.percent <= 100.0


def test_get_network_metrics():
    """Tests the get_network_metrics function."""
    metrics = get_network_metrics()
    assert isinstance(metrics, NetworkMetrics)
    assert isinstance(metrics.interfaces, dict)


def test_get_top_processes():
    """Tests the get_top_processes function."""
    count = 5
    metrics = get_top_processes(count=count)
    assert isinstance(metrics, TopProcesses)
    assert len(metrics.processes) <= count
    if metrics.processes:
        proc = metrics.processes[0]
        assert isinstance(proc.pid, int)
        assert isinstance(proc.name, str)
        assert isinstance(proc.cpu_percent, float)
        assert isinstance(proc.memory_percent, float)


def test_list_log_files():
    """Tests the list_log_files function."""
    metrics = list_log_files()
    assert isinstance(metrics, LogFiles)
    assert isinstance(metrics.files, list)
    if metrics.files:
        assert isinstance(metrics.files[0], str)


def test_get_log_records():
    """Tests the get_log_records function."""
    files_metric = list_log_files()
    if not files_metric.files:
        pytest.skip("No log files found to test.")

    filename = files_metric.files[0]
    try:
        records = get_log_records(filename, 5)
        assert isinstance(records, LogRecords)
        assert isinstance(records.records, list)
        assert len(records.records) <= 5
        if records.records:
            assert isinstance(records.records[0], str)
    except PermissionError:
        pytest.skip("Permission denied reading log file.")
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"Unexpected exception: {e}")


def test_get_log_records_not_found():
    """Tests get_log_records with a non-existent file."""
    with pytest.raises(FileNotFoundError):
        get_log_records("this_file_should_not_exist_12345.log", 5)
