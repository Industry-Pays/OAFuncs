import os
from typing import List, Optional, Union
from dask.diagnostics import ProgressBar
import xarray as xr
from oafuncs import pbar

def merge_nc(file_list: Union[str, List[str]], var_name: Optional[Union[str, List[str]]] = None, dim_name: Optional[str] = None, target_filename: Optional[str] = None) -> None:
    """
    Description:
        Merge variables from multiple NetCDF files along a specified dimension and write to a new file.
        If var_name is a string, it is considered a single variable; if it is a list and has only one element, it is also a single variable;
        If the list has more than one element, it is a multi-variable; if var_name is None, all variables are merged.

    Parameters:
        file_list: List of NetCDF file paths or a single file path as a string
        var_name: Name of the variable to be extracted or a list of variable names, default is None, which means all variables are extracted
        dim_name: Dimension name used for merging
        target_filename: Target file name after merging

    Example:
        merge(file_list, var_name='u', dim_name='time', target_filename='merged.nc')
        merge(file_list, var_name=['u', 'v'], dim_name='time', target_filename='merged.nc')
        merge(file_list, var_name=None, dim_name='time', target_filename='merged.nc')
    """
    
    if target_filename is None:
        target_filename = "merged.nc"

    # 确保目标路径存在
    target_dir = os.path.dirname(target_filename)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if isinstance(file_list, str):
        file_list = [file_list]

    # 初始化变量名列表
    if var_name is None:
        with xr.open_dataset(file_list[0]) as ds:
            var_names = list(ds.variables.keys())
    elif isinstance(var_name, str):
        var_names = [var_name]
    elif isinstance(var_name, list):
        var_names = var_name
    else:
        raise ValueError("var_name must be a string, a list of strings, or None")

    # 初始化合并数据字典
    merged_data = {}

    for i, file in pbar(enumerate(file_list), description="Reading files", color="#f8bbd0", total=len(file_list)):
        with xr.open_dataset(file) as ds:
            for var in var_names:
                data_var = ds[var]
                if dim_name in data_var.dims:
                    merged_data.setdefault(var, []).append(data_var)
                elif var not in merged_data:
                    merged_data[var] = data_var.fillna(0)  # 用0填充NaN值

    for var in pbar(merged_data, description="Merging variables", color="#9b45d1"):
        if isinstance(merged_data[var], list):
            merged_data[var] = xr.concat(merged_data[var], dim=dim_name).fillna(0)
        # print(f"Variable '{var}' merged: min={merged_data[var].min().values:.3f}, max={merged_data[var].max().values:.3f}, mean={merged_data[var].mean().values:.3f}")

    # 修改写入数据部分，支持压缩并设置基数和比例因子
    # print("\nWriting data to file ...")
    if os.path.exists(target_filename):
        print("Warning: The target file already exists. Removing it ...")
        os.remove(target_filename)

    with xr.Dataset(merged_data) as merged_dataset:
        encoding = {}
        for var in merged_dataset.data_vars:
            data = merged_dataset[var].values
            # print(f"Variable '{var}' ready for writing: min={data.min():.3f}, max={data.max():.3f}, mean={data.mean():.3f}")
            if data.dtype.kind in {"i", "u", "f"}:  # 仅对数值型数据进行压缩
                data_range = data.max() - data.min()
                if data_range > 0:  # 避免范围过小导致的精度问题
                    scale_factor = data_range / (2**16 - 1)
                    add_offset = data.min()
                    encoding[var] = {
                        "zlib": True,
                        "complevel": 4,
                        "dtype": "int16",
                        "scale_factor": scale_factor,
                        "add_offset": add_offset,
                        "_FillValue": -32767,
                    }
                else:
                    encoding[var] = {"zlib": True, "complevel": 4}  # 范围过小时禁用缩放
            else:
                encoding[var] = {"zlib": True, "complevel": 4}  # 非数值型数据不使用缩放

        # 确保写入时不会因编码问题导致数据丢失
        # merged_dataset.to_netcdf(target_filename, encoding=encoding)
        delayed_write = merged_dataset.to_netcdf(target_filename, encoding=encoding, compute=False)
        with ProgressBar():
            delayed_write.compute()

    print(f'\nFile "{target_filename}" has been successfully created.')


# Example usage
if __name__ == "__main__":
    files_to_merge = ["file1.nc", "file2.nc", "file3.nc"]
    output_path = "merged_output.nc"
    merge_nc(files_to_merge, var_name=None, dim_name="time", target_filename=output_path)
