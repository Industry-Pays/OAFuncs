import random
import re
import shutil
import sys
import threading
import time
import warnings
from collections import deque
from typing import Any, Callable, Deque, Iterable, List, NamedTuple, Optional, Union

import numpy as np
from oafuncs.oa_cmap import get as get_cmap

try:
    # import matplotlib
    from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgb
except ImportError:
    raise ImportError("This module requires matplotlib. Install with: pip install matplotlib")


class ProgressSample(NamedTuple):
    """进度采样点"""

    timestamp: float
    """采样时间戳"""
    completed: float
    """已完成步数"""


class Task:
    """进度任务信息类"""

    def __init__(
        self,
        description: str,
        total: Optional[float],
        completed: float = 0,
        visible: bool = True,
        color: Any = "cyan",
        get_time: Callable[[], float] = time.time,
    ):
        self.description = description
        self.total = total
        self.completed = completed
        self.visible = visible
        self.color = color
        self._get_time = get_time

        self.start_time: Optional[float] = None
        self.stop_time: Optional[float] = None
        self.finished_time: Optional[float] = None
        self.finished_speed: Optional[float] = None
        self._progress: Deque[ProgressSample] = deque(maxlen=1000)

    def get_time(self) -> float:
        """获取当前时间"""
        return self._get_time()

    def start(self) -> None:
        """开始任务"""
        if self.start_time is None:
            self.start_time = self.get_time()

    def stop(self) -> None:
        """停止任务"""
        if self.stop_time is None:
            self.stop_time = self.get_time()

    @property
    def started(self) -> bool:
        """任务是否已开始"""
        return self.start_time is not None

    @property
    def finished(self) -> bool:
        """任务是否已完成"""
        return self.finished_time is not None

    @property
    def percentage(self) -> float:
        """完成百分比"""
        if not self.total:
            return 0.0
        completed = (self.completed / self.total) * 100.0
        return min(100.0, max(0.0, completed))

    @property
    def elapsed(self) -> Optional[float]:
        """已用时间"""
        if self.start_time is None:
            return None
        if self.stop_time is not None:
            return self.stop_time - self.start_time
        return self.get_time() - self.start_time

    @property
    def remaining(self) -> Optional[float]:
        """剩余步数"""
        if self.total is None:
            return None
        return self.total - self.completed

    @property
    def speed(self) -> Optional[float]:
        """估计速度（步数/秒）"""
        if self.start_time is None:
            return None

        progress = self._progress
        if not progress:
            return None

        total_time = progress[-1].timestamp - progress[0].timestamp
        if total_time < 0.001:
            return None

        iter_progress = iter(progress)
        next(iter_progress)
        total_completed = sum(sample.completed for sample in iter_progress)

        speed = total_completed / total_time
        return speed

    @property
    def time_remaining(self) -> Optional[float]:
        """预估剩余时间"""
        if self.finished:
            return 0.0

        speed = self.speed
        if not speed:
            return None

        remaining = self.remaining
        if remaining is None:
            return None

        estimate = remaining / speed
        return estimate


class ColorProgressBar:
    """彩色进度条，支持多种终端环境和颜色渐变效果"""

    def __init__(
        self,
        iterable: Iterable,
        description: str = "Working ...",
        total: Optional[float] = None,
        completed: float = 0,
        color: Any = "green",
        cmap: Union[str, List[str]] = None,
        update_interval: float = 0.1,
        bar_length: int = None,
        speed_estimate_period: float = 30.0,
        next_line: bool = False,
    ):
        self.iterable = iterable
        self.description = description
        self.color = color
        self.cmap = cmap
        self.update_interval = update_interval
        self.bar_length = bar_length
        self.speed_estimate_period = speed_estimate_period
        self.next_line = next_line

        # 线程安全锁
        self._lock = threading.RLock()

        # 尝试获取总数
        if total is None and hasattr(iterable, "__len__"):
            total = len(iterable)

        # 创建任务
        self.task = Task(
            description=description,
            total=total,
            completed=completed,
            color=color,
        )

        # 输出和渲染相关
        self._file = sys.stdout
        self._gradient_colors = self._generate_gradient() if cmap and self.task.total else None
        self._last_update_time = 0

        # 检测终端环境
        self._is_terminal = hasattr(self._file, "isatty") and self._file.isatty()
        self._is_jupyter = "ipykernel" in sys.modules

        # 输出样式
        filled_list = ["▊", "█", "▓", "▒", "░", "#", "=", ">", "▌", "▍", "▎", "▏", "*"]
        self.filled = random.choice(filled_list)

    def _generate_gradient(self) -> Optional[List[str]]:
        """生成渐变色列表（修复内置colormap支持）"""
        try:
            if isinstance(self.cmap, list):
                cmap = LinearSegmentedColormap.from_list("custom_cmap", self.cmap)
            elif hasattr(self.cmap, "__call__") and hasattr(self.cmap, "N"):
                # 直接处理已经是colormap对象的情况
                cmap = self.cmap
            else:
                cmap = get_cmap(self.cmap)  # 使用oafuncs.oa_cmap.get获取内置colormap；也可获取原本自定义的colormap

            return [to_hex(cmap(i)) for i in np.linspace(0, 1, int(self.task.total))]
        except Exception as e:
            warnings.warn(f"Colormap generation failed: {str(e)}. cmap type: {type(self.cmap)}")
            return None

    def _hex_to_ansi(self, hex_color: str) -> str:
        """将颜色转换为ANSI真彩色代码"""
        try:
            rgb = [int(x * 255) for x in to_rgb(hex_color)]
            return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
        except ValueError as e:
            warnings.warn(f"Invalid color value: {e}, falling back to cyan")
            return "\033[96m"

    def _resolve_color(self, index: int) -> str:
        """解析当前应使用的颜色"""
        if self._gradient_colors:
            # 确保索引不超过颜色数
            index = min(index, len(self._gradient_colors) - 1)
            try:
                return self._hex_to_ansi(self._gradient_colors[index])
            except (IndexError, ValueError):
                pass

        return self._process_color_value(self.task.color)

    def _process_color_value(self, color: Any) -> str:
        """处理颜色输入格式"""
        preset_map = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "cyan": "\033[96m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "white": "\033[97m",
        }

        if color in preset_map:
            return preset_map[color]

        try:
            hex_color = to_hex(color)
            return self._hex_to_ansi(hex_color)
        except (ValueError, TypeError) as e:
            warnings.warn(f"Color parsing failed: {e}, using cyan")
            return preset_map["cyan"]

    def _strip_ansi(self, text: str) -> str:
        """移除所有ANSI转义序列"""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def _format_bar(self, progress: float, width: int) -> str:
        """格式化进度条显示"""
        filled = self.filled
        empty = " "
        # 为其他信息保留更多空间
        max_width = max(10, width - 60)  # 至少保留10个字符的进度条
        filled_length = int(round(max_width * progress))
        return filled * filled_length + empty * (max_width - filled_length)

    def update(self, advance: float = 1) -> None:
        """更新进度"""
        with self._lock:
            current_time = time.time()
            old_sample_time = current_time - self.speed_estimate_period

            completed_start = self.task.completed
            self.task.completed += advance
            update_completed = self.task.completed - completed_start

            # 更新速度采样
            progress = self.task._progress

            # 清理旧的采样数据
            while progress and progress[0].timestamp < old_sample_time:
                progress.popleft()

            # 添加新采样点
            if update_completed > 0:
                progress.append(ProgressSample(current_time, update_completed))

            # 检查是否完成
            if self.task.total is not None and self.task.completed >= self.task.total and self.task.finished_time is None:
                self.task.finished_time = self.task.elapsed
                self.task.finished_speed = self.task.speed

    def render(self) -> str:
        """渲染进度条"""
        with self._lock:
            # 应该在锁保护下访问task对象
            task = self.task

            # 获取终端宽度
            try:
                term_width = self.bar_length or (shutil.get_terminal_size().columns if self._is_terminal else 80)
            except (AttributeError, OSError):
                term_width = 80  # 默认终端宽度

            # 确保有效宽度不小于最低限制
            effective_width = max(15, term_width - 40)
            if effective_width < 10:
                warnings.warn("Terminal width is too small for proper progress bar rendering.")
                effective_width = 10  # 设置最低宽度限制

            # 计算进度信息
            progress = task.completed / task.total if task.total else 0
            index = int(task.completed)
            current_color = self._resolve_color(index) if self._gradient_colors else self._resolve_color(0)
            reset_code = "\033[0m"

            # 计算时间和速度信息
            elapsed = task.elapsed or 0
            remaining = task.time_remaining
            speed = task.speed or 0

            # 调整时间单位
            if elapsed >= 3600:
                elapsed_info = f"Elapsed: {elapsed / 3600:.1f}h"
            elif elapsed >= 60:
                elapsed_info = f"Elapsed: {elapsed / 60:.1f}m"
            else:
                elapsed_info = f"Elapsed: {elapsed:.1f}s"

            time_info = f"ETA: {remaining:.1f}s" if task.total and remaining and remaining > 0 else elapsed_info

            # 构建进度条视觉部分
            bar = self._format_bar(progress, effective_width)

            # 获取当前时间
            current_time = time.strftime("%H:%M:%S", time.localtime())

            # 组织显示文本
            count_info = f"{int(task.completed)}/{int(task.total)}" if task.total else str(int(task.completed))
            percent = f"{progress:.1%}" if task.total else ""
            rate_info = f"{speed:.1f}it/s" if speed else ""

            # 构建完整的进度条行
            line = f"{current_time} {self.description} {current_color}[{bar}]{reset_code} {count_info} {percent} [{time_info} | {rate_info}]"

            # 确保不超出终端宽度
            if len(self._strip_ansi(line)) > term_width:
                line = line[: term_width - 3] + "..."

            return line

    def refresh(self) -> None:
        """刷新显示进度条"""
        if not self._is_terminal and not self._is_jupyter:
            return

        with self._lock:
            line = self.render()

            # 根据环境选择不同的输出方式
            if self._is_jupyter:
                # Jupyter环境，使用换行模式
                self._file.write(f"{line}\n")
            elif self._is_terminal:
                # 标准终端环境，覆盖同一行
                if self.next_line:
                    self._file.write(f"\r{line}\n")
                else:
                    self._file.write(f"\r{line}")
            else:
                # 非交互式环境，仅在完成时输出
                if self.task.finished:
                    self._file.write(f"{line}\n")

            # 强制刷新输出
            self._file.flush()

    def __iter__(self):
        """迭代器实现，支持进度显示"""
        self.task.start()
        self._last_update_time = time.time()

        try:
            # 迭代原始可迭代对象
            for i, item in enumerate(self.iterable):
                yield item

                # 更新进度
                self.update(1)

                # 判断是否需要刷新显示
                now = time.time()
                should_refresh = (now - self._last_update_time >= self.update_interval) or (self.task.total and self.task.completed >= self.task.total)

                if should_refresh:
                    self.refresh()
                    self._last_update_time = now

        finally:
            # 完成后进行清理
            if self._is_terminal and not self._is_jupyter and not self.next_line:
                self._file.write("\n")
                self._file.flush()

    @classmethod
    def gradient_color(cls, colors: List[str], n: int) -> List[str]:
        """生成渐变色列表"""
        cmap = LinearSegmentedColormap.from_list("gradient", colors)
        return [to_hex(cmap(i)) for i in np.linspace(0, 1, n)]


def cpbar(
    iterable,
    description="Working...",
    total=None,
    completed=0,
    color="cyan",
    cmap=None,
    update_interval=0.1,
    bar_length=None,
    speed_estimate_period=30.0,
    next_line=False,
):
    """便捷函数，返回 ColorProgressBar 对象"""
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


# 验证示例
if __name__ == "__main__":
    for _ in cpbar(range(20), description="Diverging:", cmap="diverging_1", next_line=True):
        print("Processing...")
        time.sleep(0.1)

    for _ in ColorProgressBar(range(20), description="Viridis:", cmap="viridis"):
        time.sleep(0.1)

    # 使用自定义渐变色
    for _ in ColorProgressBar(range(50), description="Custom_cmap:", cmap=["#FF0000", "#0000FF"]):
        time.sleep(0.1)

    # 测试无法获取长度的迭代器
    def infinite_generator():
        i = 0
        while True:
            yield i
            i += 1

    # 限制为20个元素，但进度条不知道总长度
    gen = infinite_generator()
    for i, _ in enumerate(ColorProgressBar(gen, description="Unknown_length:")):
        if i >= 20:
            break
        time.sleep(0.1)
