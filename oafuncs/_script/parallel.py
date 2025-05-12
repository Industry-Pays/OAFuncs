import logging
import multiprocessing as mp
import platform
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple


import psutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

__all__ = ["ParallelExecutor"]


class ParallelExecutor:
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        chunk_size: Optional[int] = None,
        mem_per_process: float = 1.0,  # GB
        timeout_per_task: int = 3600,
        max_retries: int = 3,
    ):
        self.platform = self._detect_platform()
        self.mem_per_process = mem_per_process
        self.timeout_per_task = timeout_per_task
        self.max_retries = max_retries
        self.running = True
        self.task_history = []
        self._executor = None
        self._shutdown_called = False

        self.mode, default_workers = self._determine_optimal_settings()
        self.max_workers = max_workers or default_workers
        self.chunk_size = chunk_size or self._get_default_chunk_size()

        self._init_platform_settings()
        self._start_resource_monitor()

        logging.info(f"Initialized {self.__class__.__name__} on {self.platform} (mode={self.mode}, workers={self.max_workers})")

    def _detect_platform(self) -> str:
        system = platform.system().lower()
        if system == "linux":
            return "wsl" if "microsoft" in platform.release().lower() else "linux"
        return system

    def _init_platform_settings(self):
        if self.platform in ["linux", "wsl"]:
            self.mp_context = mp.get_context("fork")
        elif self.platform == "windows":
            mp.set_start_method("spawn", force=True)
            self.mp_context = mp.get_context("spawn")
        else:
            self.mp_context = None

    def _determine_optimal_settings(self) -> Tuple[str, int]:
        logical_cores = psutil.cpu_count(logical=True) or 1
        available_mem = psutil.virtual_memory().available / 1024**3  # GB

        mem_limit = max(1, int(available_mem / self.mem_per_process))
        return ("process", min(logical_cores, mem_limit))

    def _get_default_chunk_size(self) -> int:
        return max(10, 100 // (psutil.cpu_count() or 1))

    def _start_resource_monitor(self):
        def monitor():
            threshold = self.mem_per_process * 1024**3
            while self.running:
                try:
                    if psutil.virtual_memory().available < threshold:
                        self._scale_down_workers()
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"Resource monitor error: {e}")

        threading.Thread(target=monitor, daemon=True).start()

    def _scale_down_workers(self):
        if self.max_workers > 1:
            new_count = self.max_workers - 1
            logging.warning(f"Scaling down workers from {self.max_workers} to {new_count}")
            self.max_workers = new_count
            self._restart_executor()

    def _restart_executor(self):
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None

    def _get_executor(self):
        if not self._executor:
            Executor = ThreadPoolExecutor if self.mode == "thread" else ProcessPoolExecutor
            self._executor = Executor(max_workers=self.max_workers, mp_context=self.mp_context if self.mode == "process" else None)
        return self._executor

    def run(self, func: Callable, params: List[Tuple], chunk_size: Optional[int] = None) -> List[Any]:
        chunk_size = chunk_size or self.chunk_size
        try:
            for retry in range(self.max_retries + 1):
                try:
                    start_time = time.monotonic()
                    results = self._execute_batch(func, params, chunk_size)
                    self._update_settings(time.monotonic() - start_time, len(params))
                    return results
                except Exception as e:
                    logging.error(f"Attempt {retry + 1} failed: {e}")
                    self._handle_failure()
            raise RuntimeError(f"Failed after {self.max_retries} retries")
        finally:
            # 仅关闭当前 executor，保留资源监控等运行状态
            if self._executor:
                try:
                    self._executor.shutdown(wait=True)
                except Exception as e:
                    logging.error(f"Executor shutdown error: {e}")
                finally:
                    self._executor = None

    def _execute_batch(self, func: Callable, params: List[Tuple], chunk_size: int) -> List[Any]:
        from oafuncs.oa_tool import pbar
        if not params:
            return []

        if len(params) > chunk_size * 2:
            return self._chunked_execution(func, params, chunk_size)

        results = [None] * len(params)
        with self._get_executor() as executor:
            futures = {executor.submit(func, *args): idx for idx, args in enumerate(params)}
            for future in pbar(as_completed(futures), "Parallel Tasks", total=len(futures)):
                idx = futures[future]
                try:
                    results[idx] = future.result(timeout=self.timeout_per_task)
                except Exception as e:
                    results[idx] = self._handle_error(e, func, params[idx])
        return results

    def _chunked_execution(self, func: Callable, params: List[Tuple], chunk_size: int) -> List[Any]:
        results = []
        with self._get_executor() as executor:
            futures = []
            for i in range(0, len(params), chunk_size):
                chunk = params[i : i + chunk_size]
                futures.append(executor.submit(self._process_chunk, func, chunk))

            for future in as_completed(futures):
                try:
                    results.extend(future.result(timeout=self.timeout_per_task))
                except Exception as e:
                    logging.error(f"Chunk failed: {e}")
                    results.extend([None] * chunk_size)
        return results

    @staticmethod
    def _process_chunk(func: Callable, chunk: List[Tuple]) -> List[Any]:
        return [func(*args) for args in chunk]

    def _update_settings(self, duration: float, task_count: int):
        self.task_history.append((duration, task_count))
        self.chunk_size = max(5, min(100, self.chunk_size + (1 if duration < 5 else -1)))

    def _handle_error(self, error: Exception, func: Callable, args: Tuple) -> Any:
        if isinstance(error, TimeoutError):
            logging.warning(f"Timeout processing {func.__name__}{args}")
        elif isinstance(error, MemoryError):
            logging.warning("Memory error detected")
            self._scale_down_workers()
        else:
            logging.error(f"Error processing {func.__name__}{args}: {str(error)}")
        return None

    def _handle_failure(self):
        if self.max_workers > 2:
            self.max_workers = max(1, self.max_workers // 2)
            self._restart_executor()

    def shutdown(self):
        if self._shutdown_called:
            return
        self._shutdown_called = True
        self.running = False
        # 基类不再打印日志，由子类统一处理
        if self._executor:
            try:
                self._executor.shutdown(wait=True)
            except Exception as e:
                logging.error(f"Shutdown error: {e}")
            finally:
                self._executor = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.shutdown()

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "platform": self.platform,
            "mode": self.mode,
            "workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "total_tasks": sum(count for _, count in self.task_history),
        }
        if self.task_history:
            total_time = sum(time for time, _ in self.task_history)
            stats["avg_task_throughput"] = stats["total_tasks"] / total_time if total_time else 0
        return stats


def _test_func(a, b):
    time.sleep(0.01)
    return a + b


if __name__ == "__main__":
    params = [(i, i * 2) for i in range(1000)]

    with ParallelExecutor() as executor:
        results = executor.run(_test_func, params)

    # print("Results:", results)

    print(f"Processed {len(results)} tasks")
    print("Execution stats:", executor.get_stats())
