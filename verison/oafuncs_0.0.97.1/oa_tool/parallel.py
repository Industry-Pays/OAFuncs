import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

__all__ = ["ParallelExecutor"]


class ParallelExecutor:
    """
    A class for parallel execution of tasks using threads or processes.

    If mode is "process", the tasks are executed in separate processes.
    If mode is "thread", the tasks are executed in separate threads.
    
    Parameters:
        mode (str): The execution mode. Supported values are "process" and "thread".
                    process ~ Must use top function to run, can't use in jupyter notebook
                    thread ~ Function can not be top function, can use in jupyter notebook
        max_workers (int): The maximum number of workers to use. Defaults to CPU count - 1.

    Note:!!!
    If Jupyter notebook is used, the mode should be "thread" to avoid hanging issues.
    """

    def __init__(self, mode="process", max_workers=None):
        if mode not in {"process", "thread"}:
            raise ValueError("Invalid mode. Supported values are 'process' and 'thread'.")
        # process: Must use top function to run, can't use in jupyter notebook
        # thread: Can use in jupyter notebook
        self.mode = mode
        self.max_workers = max_workers or max(1, mp.cpu_count() - 1)
        self.executor_class = ProcessPoolExecutor if mode == "process" else ThreadPoolExecutor

    def run(self, func, param_list):
        """
        Run a function in parallel using the specified executor.

        Args:
            func (callable): The function to execute.
            param_list (list): A list of parameter tuples to pass to the function.

        Returns:
            list: Results of the function execution.
        """
        if not callable(func):
            raise ValueError("func must be callable.")
        if not isinstance(param_list, list) or not all(isinstance(p, tuple) for p in param_list):
            raise ValueError("param_list must be a list of tuples.")

        results = [None] * len(param_list)
        logging.info("Starting parallel execution in %s mode with %d workers.", self.mode, self.max_workers)

        with self.executor_class(max_workers=self.max_workers) as executor:
            future_to_index = {executor.submit(func, *params): idx for idx, params in enumerate(param_list)}

            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logging.error("Task %d failed with error: %s", idx, e)
                    results[idx] = e

        logging.info("Parallel execution completed.")
        return results

def _compute_square(x):
    return x * x

def _example():  
    def _compute_sum(a, b):
        return a + b

    executor1 = ParallelExecutor(mode="process", max_workers=4)
    params1 = [(i,) for i in range(10)]
    results1 = executor1.run(_compute_square, params1)
    print("Results (compute_square):", results1)

    executor2 = ParallelExecutor(mode="thread", max_workers=2)
    params2 = [(1, 2), (3, 4), (5, 6)]
    results2 = executor2.run(_compute_sum, params2)
    print("Results (compute_sum):", results2)


if __name__ == "__main__":
    _example()
    # 也可以不要装饰器，直接运行没啥问题，就是避免在ipynb中使用，最好使用ipynb，或者把这个函数放到一个独立的py文件中运行
    # 或者，jupyter中使用thread，不要使用process，因为process会导致jupyter挂掉
