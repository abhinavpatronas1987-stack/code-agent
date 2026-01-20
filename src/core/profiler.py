"""Performance Profiler - Feature 31.

Profile code execution:
- CPU profiling
- Memory profiling
- Execution time analysis
- Performance reports
"""

import cProfile
import pstats
import io
import time
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager


@dataclass
class TimingResult:
    """Result of timing an operation."""
    name: str
    elapsed_time: float  # seconds
    calls: int = 1
    avg_time: float = 0.0
    min_time: float = 0.0
    max_time: float = 0.0


@dataclass
class MemoryResult:
    """Result of memory profiling."""
    peak_memory: int  # bytes
    current_memory: int  # bytes
    allocations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FunctionProfile:
    """Profile of a function."""
    name: str
    calls: int
    total_time: float
    cumulative_time: float
    time_per_call: float
    filename: str
    line_number: int


@dataclass
class ProfileResult:
    """Result of profiling."""
    name: str
    total_time: float
    functions: List[FunctionProfile] = field(default_factory=list)
    memory: Optional[MemoryResult] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class PerformanceProfiler:
    """Performance profiling utilities."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize profiler."""
        self.storage_dir = storage_dir or Path.home() / ".code-agent" / "profiles"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timings: Dict[str, List[float]] = {}

    @contextmanager
    def timer(self, name: str):
        """
        Context manager for timing operations.

        Usage:
            with profiler.timer("my_operation"):
                do_something()
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            if name not in self.timings:
                self.timings[name] = []
            self.timings[name].append(elapsed)

    def time_function(self, func: Callable, *args, **kwargs) -> tuple:
        """
        Time a function execution.

        Args:
            func: Function to time
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            (result, elapsed_time)
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed

    def get_timing_stats(self, name: str) -> Optional[TimingResult]:
        """Get timing statistics for an operation."""
        times = self.timings.get(name)
        if not times:
            return None

        return TimingResult(
            name=name,
            elapsed_time=sum(times),
            calls=len(times),
            avg_time=sum(times) / len(times),
            min_time=min(times),
            max_time=max(times),
        )

    def clear_timings(self, name: Optional[str] = None):
        """Clear timing data."""
        if name:
            self.timings.pop(name, None)
        else:
            self.timings.clear()

    def profile_function(
        self,
        func: Callable,
        *args,
        sort_by: str = "cumulative",
        limit: int = 20,
        **kwargs
    ) -> ProfileResult:
        """
        Profile a function with cProfile.

        Args:
            func: Function to profile
            *args: Function arguments
            sort_by: Sort stat (cumulative, time, calls)
            limit: Number of results to include
            **kwargs: Function keyword arguments

        Returns:
            ProfileResult
        """
        profiler = cProfile.Profile()

        start = time.perf_counter()
        profiler.enable()
        try:
            func(*args, **kwargs)
        finally:
            profiler.disable()
        total_time = time.perf_counter() - start

        # Parse stats
        stats = pstats.Stats(profiler)
        stats.sort_stats(sort_by)

        functions = []
        for (filename, line_num, func_name), stat in list(stats.stats.items())[:limit]:
            cc, nc, tt, ct, callers = stat
            functions.append(FunctionProfile(
                name=func_name,
                calls=nc,
                total_time=tt,
                cumulative_time=ct,
                time_per_call=tt / nc if nc > 0 else 0,
                filename=filename,
                line_number=line_num,
            ))

        return ProfileResult(
            name=func.__name__ if hasattr(func, "__name__") else str(func),
            total_time=total_time,
            functions=functions,
        )

    def profile_code(
        self,
        code: str,
        globals_dict: Optional[Dict] = None,
        locals_dict: Optional[Dict] = None,
        sort_by: str = "cumulative",
        limit: int = 20,
    ) -> ProfileResult:
        """
        Profile code string.

        Args:
            code: Code to profile
            globals_dict: Global variables
            locals_dict: Local variables
            sort_by: Sort stat
            limit: Number of results

        Returns:
            ProfileResult
        """
        globals_dict = globals_dict or {}
        locals_dict = locals_dict or {}

        profiler = cProfile.Profile()

        start = time.perf_counter()
        profiler.enable()
        try:
            exec(code, globals_dict, locals_dict)
        finally:
            profiler.disable()
        total_time = time.perf_counter() - start

        # Parse stats
        stats = pstats.Stats(profiler)
        stats.sort_stats(sort_by)

        functions = []
        for (filename, line_num, func_name), stat in list(stats.stats.items())[:limit]:
            cc, nc, tt, ct, callers = stat
            functions.append(FunctionProfile(
                name=func_name,
                calls=nc,
                total_time=tt,
                cumulative_time=ct,
                time_per_call=tt / nc if nc > 0 else 0,
                filename=filename,
                line_number=line_num,
            ))

        return ProfileResult(
            name="<code>",
            total_time=total_time,
            functions=functions,
        )

    @contextmanager
    def memory_profile(self):
        """
        Context manager for memory profiling.

        Usage:
            with profiler.memory_profile() as mem:
                do_something()
            print(mem.peak_memory)
        """
        tracemalloc.start()
        result = MemoryResult(peak_memory=0, current_memory=0)

        try:
            yield result
        finally:
            current, peak = tracemalloc.get_traced_memory()
            result.current_memory = current
            result.peak_memory = peak

            # Get top allocations
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("lineno")[:10]

            for stat in top_stats:
                result.allocations.append({
                    "file": str(stat.traceback),
                    "size": stat.size,
                    "count": stat.count,
                })

            tracemalloc.stop()

    def profile_file(
        self,
        file_path: Path,
        sort_by: str = "cumulative",
        limit: int = 20,
    ) -> Optional[ProfileResult]:
        """
        Profile a Python file.

        Args:
            file_path: Path to Python file
            sort_by: Sort stat
            limit: Number of results

        Returns:
            ProfileResult or None if error
        """
        try:
            code = file_path.read_text(encoding="utf-8")
            return self.profile_code(
                code,
                {"__file__": str(file_path), "__name__": "__main__"},
                sort_by=sort_by,
                limit=limit,
            )
        except Exception as e:
            return None

    def benchmark(
        self,
        func: Callable,
        *args,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs
    ) -> TimingResult:
        """
        Benchmark a function.

        Args:
            func: Function to benchmark
            *args: Function arguments
            iterations: Number of iterations
            warmup: Warmup iterations
            **kwargs: Function keyword arguments

        Returns:
            TimingResult
        """
        # Warmup
        for _ in range(warmup):
            func(*args, **kwargs)

        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            times.append(time.perf_counter() - start)

        return TimingResult(
            name=func.__name__ if hasattr(func, "__name__") else str(func),
            elapsed_time=sum(times),
            calls=iterations,
            avg_time=sum(times) / len(times),
            min_time=min(times),
            max_time=max(times),
        )

    def format_bytes(self, size: int) -> str:
        """Format bytes to human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(size) < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def format_time(self, seconds: float) -> str:
        """Format time to human readable."""
        if seconds < 0.001:
            return f"{seconds * 1_000_000:.2f} us"
        elif seconds < 1:
            return f"{seconds * 1000:.2f} ms"
        else:
            return f"{seconds:.3f} s"

    def get_report(self, result: ProfileResult) -> str:
        """Generate profile report."""
        lines = []
        lines.append("=" * 70)
        lines.append("  PERFORMANCE PROFILE")
        lines.append("=" * 70)
        lines.append("")

        lines.append(f"Name: {result.name}")
        lines.append(f"Total Time: {self.format_time(result.total_time)}")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("")

        if result.memory:
            lines.append("Memory:")
            lines.append(f"  Peak: {self.format_bytes(result.memory.peak_memory)}")
            lines.append(f"  Current: {self.format_bytes(result.memory.current_memory)}")
            lines.append("")

        if result.functions:
            lines.append("Top Functions by Cumulative Time:")
            lines.append("-" * 70)
            lines.append(f"{'Function':<30} {'Calls':>8} {'Total':>12} {'Cumul':>12}")
            lines.append("-" * 70)

            for func in result.functions[:15]:
                name = func.name[:28] if len(func.name) > 28 else func.name
                lines.append(
                    f"{name:<30} {func.calls:>8} "
                    f"{self.format_time(func.total_time):>12} "
                    f"{self.format_time(func.cumulative_time):>12}"
                )

            if len(result.functions) > 15:
                lines.append(f"... and {len(result.functions) - 15} more functions")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def get_timings_report(self) -> str:
        """Generate report of all timings."""
        lines = []
        lines.append("=" * 60)
        lines.append("  TIMING REPORT")
        lines.append("=" * 60)
        lines.append("")

        if not self.timings:
            lines.append("No timing data recorded")
        else:
            lines.append(f"{'Operation':<30} {'Calls':>6} {'Total':>12} {'Avg':>12}")
            lines.append("-" * 60)

            for name in sorted(self.timings.keys()):
                stats = self.get_timing_stats(name)
                if stats:
                    name_display = name[:28] if len(name) > 28 else name
                    lines.append(
                        f"{name_display:<30} {stats.calls:>6} "
                        f"{self.format_time(stats.elapsed_time):>12} "
                        f"{self.format_time(stats.avg_time):>12}"
                    )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get or create profiler."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler


# Convenience functions
def profile(func: Callable, *args, **kwargs) -> ProfileResult:
    """Profile a function."""
    return get_profiler().profile_function(func, *args, **kwargs)


def benchmark(func: Callable, *args, iterations: int = 100, **kwargs) -> TimingResult:
    """Benchmark a function."""
    return get_profiler().benchmark(func, *args, iterations=iterations, **kwargs)


@contextmanager
def timer(name: str):
    """Time an operation."""
    with get_profiler().timer(name):
        yield


@contextmanager
def memory_profile():
    """Profile memory usage."""
    with get_profiler().memory_profile() as mem:
        yield mem
