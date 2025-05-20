import logging
import os
from typing import Dict, List, Union

import numpy as np
import xarray as xr
from dask.diagnostics import ProgressBar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge(file_list: Union[str, List[str]], var_name: Union[str, List[str], None] = None, dim_name: str = "time", target_filename: str = "merged.nc", chunk_config: Dict = {"time": 1000}, compression: Union[bool, Dict] = True, sanity_check: bool = True, overwrite: bool = True, parallel: bool = True) -> None:
    """
    Ultimate NetCDF merge function

    Parameters:
        file_list: List of file paths or single file path
        var_name: Variables to merge (single variable name/list of variables/None means all)
        dim_name: Dimension to merge along, default is 'time'
        target_filename: Output file path
        chunk_config: Dask chunking configuration, e.g. {"time": 1000}
        compression: Compression configuration (True enables default compression, or custom encoding dictionary)
        sanity_check: Whether to perform data integrity validation
        overwrite: Whether to overwrite existing files
        parallel: Whether to enable parallel processing

    Example:
        merge(["data1.nc", "data2.nc"],
             var_name=["temp", "salt"],
             target_filename="result.nc",
             chunk_config={"time": 500})
    """
    # ------------------------ Parameter preprocessing ------------------------#
    file_list = _validate_and_preprocess_inputs(file_list, target_filename, overwrite)
    all_vars, var_names = _determine_variables(file_list, var_name)
    static_vars = _identify_static_vars(file_list[0], var_names, dim_name)

    # Estimate required memory for processing
    _estimate_memory_usage(file_list, var_names, chunk_config)

    # ------------------------ Data validation phase ------------------------#
    if sanity_check:
        _perform_sanity_checks(file_list, var_names, dim_name, static_vars)

    # ------------------------ Core merging logic ------------------------#
    with xr.set_options(keep_attrs=True):  # Preserve metadata attributes
        # Merge dynamic variables
        merged_ds = xr.open_mfdataset(
            file_list,
            combine="nested",
            concat_dim=dim_name,
            data_vars=[var for var in var_names if var not in static_vars],
            chunks=chunk_config,
            parallel=parallel,
            preprocess=lambda ds: ds[var_names],  # Only load target variables
        )

        # Process static variables
        if static_vars:
            with xr.open_dataset(file_list[0], chunks=chunk_config) as ref_ds:
                merged_ds = merged_ds.assign({var: ref_ds[var] for var in static_vars})

    # ------------------------ Time dimension processing ------------------------#
    if dim_name == "time":
        merged_ds = _process_time_dimension(merged_ds)

    # ------------------------ File output ------------------------#
    encoding = _generate_encoding_config(merged_ds, compression)
    _write_to_netcdf(merged_ds, target_filename, encoding)


# ------------------------ Helper functions ------------------------#
def _validate_and_preprocess_inputs(file_list: Union[str, List[str]], target_filename: str, overwrite: bool) -> List[str]:
    """Input parameter validation and preprocessing"""
    if not file_list:
        raise ValueError("File list cannot be empty")

    file_list = [file_list] if isinstance(file_list, str) else file_list
    for f in file_list:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Input file does not exist: {f}")

    target_dir = os.path.dirname(os.path.abspath(target_filename))
    os.makedirs(target_dir, exist_ok=True)

    if os.path.exists(target_filename):
        if overwrite:
            logger.warning(f"Overwriting existing file: {target_filename}")
            os.remove(target_filename)
        else:
            raise FileExistsError(f"Target file already exists: {target_filename}")

    return file_list


def _determine_variables(file_list: List[str], var_name: Union[str, List[str], None]) -> tuple:
    """Determine the list of variables to process"""
    with xr.open_dataset(file_list[0]) as ds:
        all_vars = list(ds.data_vars.keys())

    if var_name is None:
        return all_vars, all_vars
    elif isinstance(var_name, str):
        if var_name not in all_vars:
            raise ValueError(f"Invalid variable name: {var_name}")
        return all_vars, [var_name]
    elif isinstance(var_name, list):
        if not var_name:  # Handle empty list case
            logger.warning("Empty variable list provided, will use all variables")
            return all_vars, all_vars
        invalid_vars = set(var_name) - set(all_vars)
        if invalid_vars:
            raise ValueError(f"Invalid variable names: {invalid_vars}")
        return all_vars, var_name
    else:
        raise TypeError("var_name parameter must be of type str/list/None")


def _identify_static_vars(sample_file: str, var_names: List[str], dim_name: str) -> List[str]:
    """Identify static variables"""
    with xr.open_dataset(sample_file) as ds:
        return [var for var in var_names if dim_name not in ds[var].dims]


def _perform_sanity_checks(file_list: List[str], var_names: List[str], dim_name: str, static_vars: List[str]) -> None:
    """Perform data integrity validation"""
    logger.info("Performing data integrity validation...")

    # Check consistency of static variables
    with xr.open_dataset(file_list[0]) as ref_ds:
        for var in static_vars:
            ref = ref_ds[var]
            for f in file_list[1:]:
                with xr.open_dataset(f) as ds:
                    if not ref.equals(ds[var]):
                        raise ValueError(f"Static variable {var} inconsistent\nReference file: {file_list[0]}\nProblem file: {f}")

    # Check dimensions of dynamic variables
    dim_sizes = {}
    for f in file_list:
        with xr.open_dataset(f) as ds:
            for var in var_names:
                if var not in static_vars:
                    dims = ds[var].dims
                    if dim_name not in dims:
                        raise ValueError(f"Variable {var} in file {f} missing merge dimension {dim_name}")
                    dim_sizes.setdefault(var, []).append(ds[var].sizes[dim_name])

    # Check dimension continuity
    for var, sizes in dim_sizes.items():
        if len(set(sizes[1:])) > 1:
            raise ValueError(f"Variable {var} has inconsistent {dim_name} dimension lengths: {sizes}")


def _process_time_dimension(ds: xr.Dataset) -> xr.Dataset:
    """Special processing for time dimension"""
    if "time" not in ds.dims:
        return ds

    # Sort and deduplicate
    ds = ds.sortby("time")
    # Find indices of unique timestamps
    _, index = np.unique(ds["time"], return_index=True)
    # No need to sort indices again as we want to keep original time order
    return ds.isel(time=index)


def _generate_encoding_config(ds: xr.Dataset, compression: Union[bool, Dict]) -> Dict:
    """Generate compression encoding configuration"""
    if not compression:
        return {}

    # Default compression settings base
    def _get_default_encoding(var):
        return {"zlib": True, "complevel": 3, "dtype": "float32" if ds[var].dtype == "float64" else ds[var].dtype}

    # Handle custom compression configuration
    encoding = {}
    if isinstance(compression, dict):
        for var in ds.data_vars:
            encoding[var] = _get_default_encoding(var)
            encoding[var].update(compression.get(var, {}))  # Use dict.update() to merge dictionaries
    else:
        for var in ds.data_vars:
            encoding[var] = _get_default_encoding(var)

    return encoding


def _calculate_file_size(filepath: str) -> str:
    """Calculate file size with adaptive unit conversion"""
    if os.path.exists(filepath):
        size_in_bytes = os.path.getsize(filepath)
        if size_in_bytes < 1e3:
            return f"{size_in_bytes:.2f} B"
        elif size_in_bytes < 1e6:
            return f"{size_in_bytes / 1e3:.2f} KB"
        elif size_in_bytes < 1e9:
            return f"{size_in_bytes / 1e6:.2f} MB"
        else:
            return f"{size_in_bytes / 1e9:.2f} GB"
    else:
        raise FileNotFoundError(f"File not found: {filepath}")


def _write_to_netcdf(ds: xr.Dataset, filename: str, encoding: Dict) -> None:
    """Improved safe writing to NetCDF file"""
    logger.info("Starting file write...")
    unlimited_dims = [dim for dim in ds.dims if ds[dim].encoding.get("unlimited", False)]

    delayed = ds.to_netcdf(filename, encoding=encoding, compute=False, unlimited_dims=unlimited_dims)

    try:
        with ProgressBar():
            delayed.compute()

        logger.info(f"Merge completed → {filename}")
        # logger.info(f"File size: {os.path.getsize(filename) / 1e9:.2f}GB")
        logger.info(f"File size: {_calculate_file_size(filename)}")
    except MemoryError as e:
        _handle_write_error(filename, "Insufficient memory to complete file write. Try adjusting chunk_config parameter to reduce memory usage", e)
    except Exception as e:
        _handle_write_error(filename, f"Failed to write file: {str(e)}", e)


def _handle_write_error(filename: str, message: str, exception: Exception) -> None:
    """Unified handling of file write exceptions"""
    logger.error(message)
    if os.path.exists(filename):
        os.remove(filename)
    raise exception


def _estimate_memory_usage(file_list: List[str], var_names: List[str], chunk_config: Dict) -> None:
    """Improved memory usage estimation"""
    try:
        total_size = 0
        sample_file = file_list[0]
        with xr.open_dataset(sample_file) as ds:
            for var in var_names:
                if var in ds:
                    # Consider variable dimension sizes
                    var_size = np.prod([ds[var].sizes[dim] for dim in ds[var].dims]) * ds[var].dtype.itemsize
                    total_size += var_size * len(file_list)

        # Estimate memory usage during Dask processing (typically 2-3x original data)
        estimated_memory = total_size * 3

        if estimated_memory > 8e9:
            logger.warning(f"Estimated memory usage may be high (approx. {estimated_memory / 1e9:.1f}GB). If memory issues occur, adjust chunk_config parameter: {chunk_config}")
    except Exception as e:
        logger.debug(f"Memory estimation failed: {str(e)}")


if __name__ == "__main__":
    # 示例文件列表（请替换为实际文件路径）
    sample_files = ["data/file1.nc", "data/file2.nc", "data/file3.nc"]

    # 示例1: 基础用法 - 合并全部变量
    print("\n" + "=" * 40)
    print("示例1: 合并所有变量（默认配置）")
    merge(file_list=sample_files, target_filename="merged_all_vars.nc")

    # 示例2: 合并指定变量
    print("\n" + "=" * 40)
    print("示例2: 合并指定变量（温度、盐度）")
    merge(
        file_list=sample_files,
        var_name=["temperature", "salinity"],
        target_filename="merged_selected_vars.nc",
        chunk_config={"time": 500},  # 更保守的内存分配
    )

    # 示例3: 自定义压缩配置
    print("\n" + "=" * 40)
    print("示例3: 自定义压缩参数")
    merge(file_list=sample_files, var_name="chlorophyll", compression={"chlorophyll": {"zlib": True, "complevel": 5, "dtype": "float32"}}, target_filename="merged_compressed.nc")

    # 示例4: 处理大型数据集
    print("\n" + "=" * 40)
    print("示例4: 大文件分块策略")
    merge(file_list=sample_files, chunk_config={"time": 2000, "lat": 100, "lon": 100}, target_filename="merged_large_dataset.nc", parallel=True)

    # 示例5: 时间维度特殊处理
    print("\n" + "=" * 40)
    print("示例5: 时间维度排序去重")
    merge(
        file_list=sample_files,
        dim_name="time",
        target_filename="merged_time_processed.nc",
        sanity_check=True,  # 强制数据校验
    )

    # 示例6: 覆盖已存在文件
    print("\n" + "=" * 40)
    print("示例6: 强制覆盖现有文件")
    try:
        merge(
            file_list=sample_files,
            target_filename="merged_all_vars.nc",  # 与示例1相同文件名
            overwrite=True,  # 显式启用覆盖
        )
    except FileExistsError as e:
        print(f"捕获预期外异常: {str(e)}")

    # 示例7: 禁用并行处理
    print("\n" + "=" * 40)
    print("示例7: 单线程模式运行")
    merge(file_list=sample_files, target_filename="merged_single_thread.nc", parallel=False)

    # 示例8: 处理特殊维度
    print("\n" + "=" * 40)
    print("示例8: 按深度维度合并")
    merge(file_list=sample_files, dim_name="depth", var_name=["density", "oxygen"], target_filename="merged_by_depth.nc")

    # 示例9: 混合变量类型处理
    print("\n" + "=" * 40)
    print("示例9: 混合静态/动态变量")
    merge(
        file_list=sample_files,
        var_name=["bathymetry", "temperature"],  # bathymetry为静态变量
        target_filename="merged_mixed_vars.nc",
        sanity_check=True,  # 验证静态变量一致性
    )

    # 示例10: 完整配置演示
    print("\n" + "=" * 40)
    print("示例10: 全参数配置演示")
    merge(
        file_list=sample_files,
        var_name=None,  # 所有变量
        dim_name="time",
        target_filename="merged_full_config.nc",
        chunk_config={"time": 1000, "lat": 500, "lon": 500},
        compression={"temperature": {"complevel": 4}, "salinity": {"zlib": False}},
        sanity_check=True,
        overwrite=True,
        parallel=True,
    )
