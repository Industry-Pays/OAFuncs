import datetime
import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union


from rich import print

from ._script.parallel import ParallelExecutor

__all__ = ["PEx", "email", "pbar"]


class PEx(ParallelExecutor):
    """
    并行执行器扩展类 (ParallelExecutor Extend)

    继承自 ParallelExecutor，提供更简洁的接口和增强功能：

    特点：
    - 自动时间统计 (开始/结束时间、总耗时)
    - 增强的错误处理机制
    - 友好的统计输出格式
    - 支持进度回调函数

    示例：
    >>> with PEx() as executor:
    ...     results = executor.run(lambda x: x*2, [(i,) for i in range(5)])
    ...     print(executor.format_stats())
    [2024-06-08 15:30:00] 成功处理5个任务 (耗时0.5秒)

    参数调整建议：
    - 内存密集型任务：增大 mem_per_process
    - I/O密集型任务：使用 mode='thread'
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        chunk_size: Optional[int] = None,
        mem_per_process: float = 1.5,  # 调大默认内存限制
        timeout_per_task: int = 7200,  # 延长默认超时时间
        max_retries: int = 5,  # 增加默认重试次数
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """
        初始化并行执行器

        :param max_workers: 最大工作进程/线程数 (默认自动计算)
        :param chunk_size: 任务分块大小 (默认自动优化)
        :param mem_per_process: 单进程内存预估(GB)
        :param timeout_per_task: 单任务超时时间(秒)
        :param max_retries: 最大重试次数
        :param progress_callback: 进度回调函数 (当前完成数, 总数)
        """
        # 时间记录扩展
        self.start_dt = datetime.datetime.now()
        self.end_dt = None
        self.progress_callback = progress_callback

        super().__init__(max_workers=max_workers, chunk_size=chunk_size, mem_per_process=mem_per_process, timeout_per_task=timeout_per_task, max_retries=max_retries)

        logging.info(f"PEx initialized at {self.start_dt:%Y-%m-%d %H:%M:%S}")

    def run(self, func: Callable, params: List[Tuple], chunk_size: Optional[int] = None) -> List[Any]:
        """
        执行并行任务 (增强版)

        :param func: 目标函数，需能序列化(pickle)
        :param params: 参数列表，每个元素为参数元组
        :param chunk_size: 可选的分块大小
        :return: 结果列表，与输入顺序一致
        """
        total_tasks = len(params)
        if self.progress_callback:
            self.progress_callback(0, total_tasks)

        results = super().run(func, params, chunk_size)

        if self.progress_callback:
            self.progress_callback(total_tasks, total_tasks)

        return results

    def shutdown(self):
        """增强关闭方法，记录结束时间"""
        self.end_dt = datetime.datetime.now()
        super().shutdown()
        logging.info(f"PEx shutdown at {self.end_dt:%Y-%m-%d %H:%M:%S}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息 (扩展时间数据)"""
        stats = super().get_stats()
        stats.update({"start_time": self.start_dt.strftime("%Y-%m-%d %H:%M:%S"), "end_time": self.end_dt.strftime("%Y-%m-%d %H:%M:%S") if self.end_dt else "运行中", "total_seconds": round((self.end_dt - self.start_dt).total_seconds(), 3) if self.end_dt else None})
        return stats

    def format_stats(self) -> str:
        """生成友好统计报告"""
        stats = self.get_stats()
        report = [
            f"[{stats['start_time']}] 并行任务统计报告",
            f"▪ 平台环境：{stats['platform'].upper()} ({stats['mode']}模式)",
            f"▪ 资源使用：{stats['workers']}个工作进程 | 分块大小{stats['chunk_size']}",
            f"▪ 任务统计：成功处理{stats['total_tasks']}个任务 (失败{stats['total_tasks'] - sum(1 for r in self.results if r is not None)})",
            f"▪ 时间统计：总耗时{stats['total_seconds']}秒",
        ]
        if "avg_task_throughput" in stats:
            report.append(f"▪ 吞吐性能：{stats['avg_task_throughput']:.1f} 任务/秒")
        return "\n".join(report)

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动关闭"""
        self.shutdown()




def email(title: str = "Title", content: Optional[str] = None, send_to: str = "10001@qq.com") -> None:
    """
    Send an email using the specified title, content, and recipient.

    Args:
        title (str): The title of the email. Defaults to "Title".
        content (Optional[str]): The content of the email. Defaults to None.
        send_to (str): The recipient's email address. Defaults to "10001@qq.com".
    """
    from ._script.email import send

    print(f"[green]Sending email to {send_to} with title: {title}[/green]")
    send(title, content, send_to)


def pbar(
    iterable: Iterable = range(100),
    description: str = None,
    total: Optional[float] = None,
    completed: float = 0,
    color: Any = "None",
    cmap: Union[str, List[str], None] = None,
    update_interval: float = 0.1,
    bar_length: Optional[int] = None,
    speed_estimate_period: float = 30.0,
    next_line: bool = False,
) -> Any:
    """
    Convenience function to return a ColorProgressBar object.

    Args:
        iterable (Iterable): The iterable to track progress for. Defaults to range(100).
        description (str): Description text for the progress bar. Defaults to "Working...".
        total (Optional[float]): Total number of iterations. Defaults to None.
        completed (float): Number of completed iterations. Defaults to 0.
        color (Any): Color of the progress bar. Defaults to "cyan".
        cmap (Union[str, List[str], None]): Color map for the progress bar. Defaults to None.
        update_interval (float): Interval for updating the progress bar. Defaults to 0.1.
        bar_length (Optional[int]): Length of the progress bar. Defaults to None.
        speed_estimate_period (float): Period for speed estimation. Defaults to 30.0.
        next_line (bool): Whether to move to the next line after completion. Defaults to False.

    Returns:
        Any: An instance of ColorProgressBar.
    """
    from ._script.cprogressbar import ColorProgressBar
    import random

    def _generate_random_color_hex():
        """Generate a random color in hexadecimal format."""
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return '#{r:02x}{g:02x}{b:02x}'.format(r=r, g=g, b=b)

    if color == 'None' and cmap is None:
        color = _generate_random_color_hex()

    if description is not None:
        style = f"bold {color if color != 'None' else 'green'}"
        print(f"[{style}]~*^* {description} *^*~[/{style}]")

    description = ""
    
    return ColorProgressBar(
        iterable=iterable,
        description=description,
        total=total,
        completed=completed,
        color=color,
        cmap=cmap,
        update_interval=update_interval,
        bar_length=bar_length,
        speed_estimate_period=speed_estimate_period,
        next_line=next_line,
    )


# 使用示例
if __name__ == "__main__":

    def sample_task(x):
        import time

        time.sleep(0.1)
        return x * 2

    def progress_handler(current, total):
        print(f"\r进度: {current}/{total} ({current / total:.1%})", end="")

    with PEx(max_workers=4, progress_callback=progress_handler) as executor:
        results = executor.run(sample_task, [(i,) for i in range(10)])

    print("\n" + executor.format_stats())