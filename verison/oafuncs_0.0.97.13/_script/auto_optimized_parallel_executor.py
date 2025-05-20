import contextlib
import logging
import multiprocessing as mp
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import psutil


class ParallelExecutor:
    """
    自动优化的并行执行器，根据平台和任务特性自动选择最佳执行模式和工作线程/进程数量。

    特性:
    - 自动检测平台并选择最佳执行模式
    - 动态调整工作线程/进程数量
    - 针对Linux和Windows的特定优化
    - 任务批处理功能以提高小任务的效率
    - 自动故障转移机制
    """

    def __init__(self):
        # 检测平台
        self.platform = self._detect_platform()
        # 自动选择最佳执行模式和工作线程/进程数量
        self.mode, self.max_workers = self._determine_optimal_settings()
        # 初始化执行器
        self._executor = None
        self.executor_class = ProcessPoolExecutor if self.mode == "process" else ThreadPoolExecutor
        # 进程池重用策略
        self.reuse_pool = self.mode == "process" and self.platform != "windows"

        # 特定于平台的优化参数
        self.mp_context = None
        self.chunk_size = self._get_default_chunk_size()
        self.timeout_per_task = 3600  # 默认任务超时时间（秒）
        self.worker_init_func = None

        # 针对Linux的特定优化
        if self.platform == "linux":
            self._setup_linux_optimizations()
        # 针对Windows的特定优化
        elif self.platform == "windows":
            self._setup_windows_optimizations()

        logging.info(f"Initialized {self.__class__.__name__} with mode={self.mode}, max_workers={self.max_workers} on {self.platform} platform")

    def _detect_platform(self):
        """检测当前运行的平台"""
        system = platform.system().lower()
        if system == "linux":
            return "linux"
        elif system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        else:
            return "unknown"

    def _determine_optimal_settings(self):
        """确定最佳执行模式和工作线程/进程数量"""
        mode = "process"  # 默认使用进程模式

        # Linux平台优化
        if self.platform == "linux":
            # 在Linux上，根据之前的问题，我们优先使用进程模式
            mode = "process"

            # 检查是否在容器中运行（如Docker）
            in_container = self._is_in_container()

            # 获取物理和逻辑CPU核心数
            physical_cores = psutil.cpu_count(logical=False) or 1
            logical_cores = psutil.cpu_count(logical=True) or 1

            # 获取系统内存信息
            mem = psutil.virtual_memory()
            total_mem_gb = mem.total / (1024**3)
            available_mem_gb = mem.available / (1024**3)

            # 每个进程估计内存使用（根据应用程序特性调整）
            est_mem_per_process_gb = 0.5

            # 根据可用内存限制工作进程数
            mem_limited_workers = max(1, int(available_mem_gb / est_mem_per_process_gb))

            # 在容器环境中更保守一些
            if in_container:
                max_workers = min(physical_cores, mem_limited_workers, 4)
            else:
                max_workers = min(logical_cores, mem_limited_workers)

        # Windows平台优化
        elif self.platform == "windows":
            # Windows上进程创建较快，线程和进程都可以考虑
            # 但进程间通信开销大，所以对于小型任务，线程可能更高效
            mode = "process"  # 默认也使用进程模式，因为通常更可靠

            # Windows通常使用超线程，所以我们可以使用逻辑核心数
            logical_cores = psutil.cpu_count(logical=True) or 1

            # Windows建议使用更少的进程以减少开销
            if logical_cores > 4:
                max_workers = logical_cores - 1
            else:
                max_workers = max(1, logical_cores)

        # macOS平台优化
        elif self.platform == "macos":
            mode = "process"
            logical_cores = psutil.cpu_count(logical=True) or 1
            max_workers = max(1, logical_cores - 1)

        # 未知平台的保守设置
        else:
            mode = "process"
            max_workers = max(1, (psutil.cpu_count(logical=True) or 2) - 1)

        return mode, max_workers

    def _is_in_container(self):
        """检测是否在容器环境中运行"""
        # 检查常见的容器环境指标
        if os.path.exists("/.dockerenv"):
            return True

        try:
            with open("/proc/1/cgroup", "rt") as f:
                return any(("docker" in line or "kubepods" in line) for line in f)
        except:
            pass

        return False

    def _setup_linux_optimizations(self):
        """设置Linux特定的优化参数"""
        try:
            # 在Linux上，选择最适合的多进程上下文
            # fork: 最快但可能会导致多线程程序出现问题
            # spawn: 更安全但更慢
            # forkserver: 中间解决方案

            # 根据应用程序特性选择合适的上下文
            self.mp_context = mp.get_context("fork")

            # 设置进程初始化函数来设置CPU亲和性
            self.worker_init_func = self._linux_worker_init

        except Exception as e:
            logging.warning(f"Failed to set Linux optimizations: {e}")
            self.mp_context = None

    def _setup_windows_optimizations(self):
        """设置Windows特定的优化参数"""
        # Windows优化参数
        # 进程创建和启动开销在Windows上较高，因此增加每批的任务数
        self.chunk_size = 10
        # Windows通常不需要特殊的工作进程初始化
        self.worker_init_func = None

    def _linux_worker_init(self):
        """Linux工作进程初始化函数"""
        try:
            # 获取当前进程
            p = psutil.Process()

            # 设置进程优先级为稍低于正常，以避免争抢重要系统资源
            p.nice(10)

            # 尝试设置CPU亲和性以提高缓存局部性
            # 这里我们不设置特定的CPU核心，让系统调度，因为手动设置可能导致不平衡

            # 设置进程I/O优先级
            # 需要root权限，所以只是尝试一下
            try:
                os.system(f"ionice -c 2 -n 4 -p {os.getpid()} > /dev/null 2>&1")
            except:
                pass

        except Exception as e:
            logging.debug(f"Worker initialization warning (non-critical): {e}")
            pass  # 失败不中断程序运行

    def _get_default_chunk_size(self):
        """获取默认任务分块大小"""
        if self.platform == "linux":
            # Linux下进程创建较快，可以使用较小的块大小
            return 5
        elif self.platform == "windows":
            # Windows下进程创建较慢，使用较大的块大小
            return 10
        else:
            return 5

    @property
    def executor(self):
        """懒加载并重用执行器"""
        if self._executor is None and self.reuse_pool:
            kwargs = {}
            if self.mode == "process" and self.mp_context:
                kwargs["mp_context"] = self.mp_context

            if self.worker_init_func and self.mode == "process":
                kwargs["initializer"] = self.worker_init_func

            self._executor = self.executor_class(max_workers=self.max_workers, **kwargs)
        return self._executor

    @contextlib.contextmanager
    def get_executor(self):
        """获取执行器的上下文管理器"""
        if self.reuse_pool and self._executor:
            yield self._executor
        else:
            kwargs = {}
            if self.mode == "process" and self.mp_context:
                kwargs["mp_context"] = self.mp_context

            if self.worker_init_func and self.mode == "process":
                kwargs["initializer"] = self.worker_init_func

            with self.executor_class(max_workers=self.max_workers, **kwargs) as executor:
                yield executor

    def run(self, func, param_list, chunk_size=None, fallback_on_failure=True):
        """
        并行执行函数

        Args:
            func (callable): 要执行的函数
            param_list (list): 参数元组列表
            chunk_size (int, optional): 任务分块大小，None表示使用默认值
            fallback_on_failure (bool): 如果主执行模式失败，是否尝试其他模式

        Returns:
            list: 函数执行结果
        """
        if not callable(func):
            raise ValueError("func must be callable.")
        if not isinstance(param_list, list):
            raise ValueError("param_list must be a list.")

        # 空列表直接返回
        if not param_list:
            return []

        # 使用默认分块大小或自定义大小
        effective_chunk_size = chunk_size or self.chunk_size

        # 任务分块处理
        if effective_chunk_size and len(param_list) > effective_chunk_size * 2:
            return self._run_chunked(func, param_list, effective_chunk_size)

        try:
            return self._execute(func, param_list)
        except Exception as e:
            if fallback_on_failure:
                logging.warning(f"Execution failed with {self.mode} mode: {e}. Trying fallback...")
                # 如果当前模式失败，尝试其他模式
                old_mode = self.mode
                self.mode = "thread" if old_mode == "process" else "process"
                self.executor_class = ProcessPoolExecutor if self.mode == "process" else ThreadPoolExecutor
                self._executor = None  # 重置执行器

                try:
                    results = self._execute(func, param_list)
                    logging.info(f"Fallback to {self.mode} mode succeeded.")
                    return results
                except Exception as e2:
                    logging.error(f"Fallback also failed: {e2}")
                    # 恢复原始模式
                    self.mode = old_mode
                    self.executor_class = ProcessPoolExecutor if self.mode == "process" else ThreadPoolExecutor
                    self._executor = None
                    raise
            else:
                raise

    def _execute(self, func, param_list):
        """内部执行方法"""
        results = [None] * len(param_list)
        logging.info("Starting parallel execution in %s mode with %d workers.", self.mode, self.max_workers)

        start_time = time.time()

        with self.get_executor() as executor:
            future_to_index = {executor.submit(func, *params): idx for idx, params in enumerate(param_list)}

            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    # 添加超时保护
                    results[idx] = future.result(timeout=self.timeout_per_task)
                except Exception as e:
                    logging.error("Task %d failed with error: %s", idx, e)
                    results[idx] = e

        elapsed = time.time() - start_time
        logging.info("Parallel execution completed in %.2f seconds.", elapsed)
        return results

    def _run_chunked(self, func, param_list, chunk_size):
        """处理大量小任务的批处理执行"""

        def process_chunk(chunk):
            return [func(*params) for params in chunk]

        # 将参数列表分成多个块
        chunks = [param_list[i : i + chunk_size] for i in range(0, len(param_list), chunk_size)]

        logging.info(f"Processing {len(param_list)} tasks in {len(chunks)} chunks of size ~{chunk_size}")

        chunk_results = self._execute(process_chunk, [(chunk,) for chunk in chunks])

        # 将块结果展平成单个结果列表
        return [result for sublist in chunk_results if isinstance(sublist, list) for result in sublist]

    def map(self, func, *iterables, timeout=None, chunk_size=None):
        """
        类似于内置map函数的并行版本

        Args:
            func: 要应用于每个元素的函数
            *iterables: 一个或多个可迭代对象
            timeout: 每个任务的超时时间
            chunk_size: 任务分块大小

        Returns:
            生成器，产生的结果与输入顺序相同
        """
        # 将zip后的可迭代对象转换为参数元组列表
        param_list = [(args,) for args in zip(*iterables)]

        # 临时存储超时设置
        original_timeout = self.timeout_per_task
        if timeout:
            self.timeout_per_task = timeout

        try:
            results = self.run(lambda x: func(x), param_list, chunk_size=chunk_size)
            for r in results:
                yield r
        finally:
            # 恢复原超时设置
            self.timeout_per_task = original_timeout

    def __del__(self):
        """确保资源被正确释放"""
        self.shutdown()

    def shutdown(self):
        """显式关闭执行器"""
        if self._executor:
            try:
                self._executor.shutdown(wait=True)
            except:
                pass
            self._executor = None

    def imap(self, func, *iterables, timeout=None, chunk_size=None):
        """
        类似concurrent.futures.Executor.map的接口，但返回迭代器
        """
        return self.map(func, *iterables, timeout=timeout, chunk_size=chunk_size)

    def imap_unordered(self, func, *iterables, timeout=None, chunk_size=None):
        """
        类似multiprocessing.Pool.imap_unordered的接口，结果可能乱序返回
        """
        # 将zip后的可迭代对象转换为参数元组列表
        param_list = [(args,) for args in zip(*iterables)]

        # 空列表直接返回
        if not param_list:
            return

        # 临时存储超时设置
        original_timeout = self.timeout_per_task
        if timeout:
            self.timeout_per_task = timeout

        try:
            # 使用默认分块大小或自定义大小
            effective_chunk_size = chunk_size or self.chunk_size

            # 任务分块处理
            if effective_chunk_size and len(param_list) > effective_chunk_size * 2:
                chunks = [param_list[i : i + effective_chunk_size] for i in range(0, len(param_list), effective_chunk_size)]

                with self.get_executor() as executor:
                    futures = [executor.submit(self._process_chunk_for_imap, func, chunk) for chunk in chunks]

                    for future in as_completed(futures):
                        try:
                            chunk_results = future.result(timeout=self.timeout_per_task)
                            for result in chunk_results:
                                yield result
                        except Exception as e:
                            logging.error(f"Chunk processing failed: {e}")
            else:
                with self.get_executor() as executor:
                    futures = [executor.submit(func, *params) for params in param_list]

                    for future in as_completed(futures):
                        try:
                            yield future.result(timeout=self.timeout_per_task)
                        except Exception as e:
                            logging.error(f"Task failed: {e}")
                            yield e
        finally:
            # 恢复原超时设置
            self.timeout_per_task = original_timeout

    def _process_chunk_for_imap(self, func, chunk):
        """处理imap_unordered的数据块"""
        return [func(*params) for params in chunk]

    def starmap(self, func, iterable, timeout=None, chunk_size=None):
        """
        类似于内置starmap函数的并行版本

        Args:
            func: 要应用于每个元素的函数
            iterable: 可迭代对象，每个元素是函数参数的元组
            timeout: 每个任务的超时时间
            chunk_size: 任务分块大小

        Returns:
            生成器，产生结果
        """

        # 将每个元素转换为单参数函数调用
        def wrapper(args):
            return func(*args)

        # 使用map实现
        return self.map(wrapper, iterable, timeout=timeout, chunk_size=chunk_size)

    def gather(self, funcs_and_args):
        """
        并行执行多个不同的函数，类似于asyncio.gather

        Args:
            funcs_and_args: 列表，每个元素是(func, args)元组，
                            其中args是要传递给func的参数元组

        Returns:
            list: 函数执行结果，顺序与输入相同
        """
        if not isinstance(funcs_and_args, list):
            raise ValueError("funcs_and_args must be a list of (func, args) tuples")

        def wrapper(func_and_args):
            func, args = func_and_args
            return func(*args)

        return self.run(wrapper, [(item,) for item in funcs_and_args])
