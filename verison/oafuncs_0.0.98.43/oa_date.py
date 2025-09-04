import calendar
import datetime
import functools
from typing import List, Optional

from rich import print

__all__ = ["month_days", "hour_range", "adjust_time", "timeit"]


def month_days(year: int, month: int) -> int:
    """
    Calculate the number of days in a specific month of a year.

    Args:
        year (int): The year.
        month (int): The month (1-12).

    Returns:
        int: Number of days in the specified month.

    Example:
        >>> month_days(2024, 2)
        29
    """
    return calendar.monthrange(year, month)[1]


def hour_range(start_time: str, end_time: str, hour_interval: int = 6) -> List[str]:
    """
    Generate a list of datetime strings with a specified interval in hours.

    Args:
        start_time (str): Start date in the format "%Y%m%d%H".
        end_time (str): End date in the format "%Y%m%d%H".
        hour_interval (int): Interval in hours between each datetime.

    Returns:
        List[str]: List of datetime strings in the format "%Y%m%d%H".

    Example:
        >>> hour_range("2024010100", "2024010200", 6)
        ['2024010100', '2024010106', '2024010112', '2024010118', '2024010124']
    """
    date_s = datetime.datetime.strptime(start_time, "%Y%m%d%H")
    date_e = datetime.datetime.strptime(end_time, "%Y%m%d%H")
    date_list = []
    while date_s <= date_e:
        date_list.append(date_s.strftime("%Y%m%d%H"))
        date_s += datetime.timedelta(hours=hour_interval)
    return date_list


def adjust_time(base_time: str, time_delta: int, delta_unit: str = "hours", output_format: Optional[str] = None) -> str:
    """
    Adjust a given base time by adding a specified time delta.

    Args:
        base_time (str): Base time in the format "yyyy" to "yyyymmddHHMMSS".
                         Missing parts are padded with appropriate defaults.
        time_delta (int): The amount of time to add.
        delta_unit (str): The unit of time to add ("seconds", "minutes", "hours", "days", "months", "years").
        output_format (str, optional): Custom output format for the adjusted time. Defaults to None.

    Returns:
        str: The adjusted time as a string, formatted according to the output_format or time unit.

    Example:
        >>> adjust_time("20240101", 5, "days")
        '20240106'
        >>> adjust_time("20240101000000", 2, "hours", "%Y-%m-%d %H:%M:%S")
        '2024-01-01 02:00:00'
        >>> adjust_time("20240101000000", 30, "minutes")
        '20240101003000'
    """
    # Normalize the input time to "yyyymmddHHMMSS" format
    time_format = "%Y%m%d%H%M%S"

    # Pad the time string to full format
    if len(base_time) == 4:  # yyyy
        base_time += "0101000000"
    elif len(base_time) == 6:  # yyyymm
        base_time += "01000000"
    elif len(base_time) == 8:  # yyyymmdd
        base_time += "000000"
    elif len(base_time) == 10:  # yyyymmddhh
        base_time += "0000"
    elif len(base_time) == 12:  # yyyymmddhhmm
        base_time += "00"
    elif len(base_time) == 14:  # yyyymmddhhmmss
        pass  # Already complete
    else:
        raise ValueError(f"Invalid base_time format. Expected 4-14 digits, got {len(base_time)}")

    try:
        time_obj = datetime.datetime.strptime(base_time, time_format)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {base_time}. Error: {e}")

    # Add the specified amount of time
    if delta_unit == "seconds":
        time_obj += datetime.timedelta(seconds=time_delta)
    elif delta_unit == "minutes":
        time_obj += datetime.timedelta(minutes=time_delta)
    elif delta_unit == "hours":
        time_obj += datetime.timedelta(hours=time_delta)
    elif delta_unit == "days":
        time_obj += datetime.timedelta(days=time_delta)
    elif delta_unit == "months":
        # Handle month addition separately
        month = time_obj.month - 1 + time_delta
        year = time_obj.year + month // 12
        month = month % 12 + 1
        day = min(time_obj.day, month_days(year, month))
        time_obj = time_obj.replace(year=year, month=month, day=day)
    elif delta_unit == "years":
        # Handle year addition separately
        try:
            year = time_obj.year + time_delta
            # Handle leap year edge case for Feb 29
            if time_obj.month == 2 and time_obj.day == 29:
                if not calendar.isleap(year):
                    time_obj = time_obj.replace(year=year, day=28)
                else:
                    time_obj = time_obj.replace(year=year)
            else:
                time_obj = time_obj.replace(year=year)
        except ValueError as e:
            raise ValueError(f"Invalid year calculation: {e}")
    else:
        raise ValueError("Invalid time unit. Use 'seconds', 'minutes', 'hours', 'days', 'months', or 'years'.")

    # Determine the output format
    if output_format:
        return time_obj.strftime(output_format)
    else:
        # Use default format based on delta_unit
        format_map = {"seconds": "%Y%m%d%H%M%S", "minutes": "%Y%m%d%H%M%S", "hours": "%Y%m%d%H", "days": "%Y%m%d", "months": "%Y%m", "years": "%Y"}
        return time_obj.strftime(format_map[delta_unit])


class timeit:
    """
    A decorator to measure the execution time of a function.

    Usage:
        @timeit(log_to_file=True, display_time=True)
        def my_function():
            # Function code here

    Args:
        log_to_file (bool): Whether to log the execution time to a file. Defaults to False.
        display_time (bool): Whether to print the execution time to the console. Defaults to True.

    Example:
        @timeit(log_to_file=True, display_time=True)
        def example_function():
            import time
            time.sleep(2)
    """

    def __init__(self, log_to_file: bool = False, display_time: bool = True):
        self.log_to_file = log_to_file
        self.display_time = display_time

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()

            if self.display_time:
                print(f"[bold green]Function '{func.__name__}' executed in {elapsed_time:.2f} seconds.[/bold green]")

            if self.log_to_file:
                with open("execution_time.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.datetime.now()} - Function '{func.__name__}' executed in {elapsed_time:.2f} seconds.\n")

            return result

        return wrapper
