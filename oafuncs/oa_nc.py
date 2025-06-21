import os
from typing import List, Optional, Tuple, Union

import numpy as np
import xarray as xr
from rich import print

__all__ = ["save", "merge", "modify", "rename", "check", "convert_longitude", "isel", "draw", "compress", "unscale"]



def save(
    file_path: str,
    data: Union[np.ndarray, xr.DataArray, xr.Dataset],
    variable_name: Optional[str] = None,
    coordinates: Optional[dict] = None,
    write_mode: str = "w",
    convert_dtype: str = "int32",
    use_scale_offset: bool = True,
    use_compression: bool = True,
    preserve_mask_values: bool = True,
) -> None:
    """
    Write data to a NetCDF file.

    Args:
        file_path (str): File path to save the NetCDF file.
        data (Union[np.ndarray, xr.DataArray, xr.Dataset]): Data to be written.
        variable_name (Optional[str]): Variable name for the data.
        coordinates (Optional[dict]): Coordinates, where keys are dimension names and values are coordinate data.
        write_mode (str): Write mode, 'w' for write, 'a' for append. Default is 'w'.
        convert_dtype (str): Data type to convert to. Default is 'int32'.
        use_scale_offset (bool): Whether to use scale_factor and add_offset. Default is True.
        use_compression (bool): Whether to use compression parameters. Default is True.
        preserve_mask_values (bool): Whether to preserve mask values. Default is True.

    Example:
        >>> save(r'test.nc', data, 'u', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')
        >>> save(r'test.nc', data, 'u', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'w')
        >>> save(r'test.nc', data, 'u', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'w', use_scale_offset=False, use_compression=False)
        >>> save(r'test.nc', data)
    """
    from ._script.netcdf_write import save_to_nc

    save_to_nc(file_path, data, variable_name, coordinates, write_mode, convert_dtype,use_scale_offset, use_compression, preserve_mask_values)
    print(f"[green]Data successfully saved to {file_path}[/green]")


def merge(
    file_paths: Union[str, List[str]],
    variable_names: Optional[Union[str, List[str]]] = None,
    merge_dimension: Optional[str] = None,
    output_file: Optional[str] = None,
) -> None:
    """
    Merge multiple NetCDF files into one.

    Args:
        file_paths (Union[str, List[str]]): List of file paths or a single file path.
        variable_names (Optional[Union[str, List[str]]]): Variable names to merge.
        merge_dimension (Optional[str]): Dimension name to merge along.
        output_file (Optional[str]): Output file name.

    Example:
        merge(['file1.nc', 'file2.nc'], variable_names='temperature', merge_dimension='time', output_file='merged.nc')
    """
    from ._script.netcdf_merge import merge_nc

    merge_nc(file_paths, variable_names, merge_dimension, output_file)
    print(f"[green]Files successfully merged into {output_file}[/green]")


def modify(
    file_path: str,
    variable_name: str,
    attribute_name: Optional[str] = None,
    new_value: Optional[Union[str, float, int, np.ndarray]] = None,
) -> None:
    """
    Modify the value of a variable or an attribute in a NetCDF file.

    Args:
        file_path (str): Path to the NetCDF file.
        variable_name (str): Name of the variable to be modified.
        attribute_name (Optional[str]): Name of the attribute to be modified. If None, the variable value will be modified.
        new_value (Optional[Union[str, float, int, np.ndarray]]): New value for the variable or attribute.

    Example:
        >>> modify('file.nc', 'temperature', 'units', 'Celsius')
        >>> modify('file.nc', 'temperature', new_value=np.array([1, 2, 3]))
    """
    from ._script.netcdf_modify import modify_nc

    modify_nc(file_path, variable_name, attribute_name, new_value)
    print(f"[green]Successfully modified {variable_name} in {file_path}[/green]")


def rename(
    file_path: str,
    old_name: str,
    new_name: str,
) -> None:
    """
    Rename a variable or dimension in a NetCDF file.

    Args:
        file_path (str): Path to the NetCDF file.
        old_name (str): Current name of the variable or dimension.
        new_name (str): New name to assign to the variable or dimension.

    Example:
        >>> rename('file.nc', 'old_var', 'new_var')
    """
    import netCDF4 as nc
    try:
        with nc.Dataset(file_path, "r+") as dataset:
            if old_name not in dataset.variables and old_name not in dataset.dimensions:
                print(f"[yellow]Variable or dimension {old_name} not found in the file.[/yellow]")
                return

            if old_name in dataset.variables:
                dataset.renameVariable(old_name, new_name)
                print(f"[green]Successfully renamed variable {old_name} to {new_name}.[/green]")

            if old_name in dataset.dimensions:
                if new_name in dataset.dimensions:
                    raise ValueError(f"Dimension name {new_name} already exists in the file.")
                dataset.renameDimension(old_name, new_name)
                print(f"[green]Successfully renamed dimension {old_name} to {new_name}.[/green]")

    except Exception as e:
        print(f"[red]An error occurred: {e}[/red]")


def check(
    file_path: str,
    delete_if_invalid: bool = False,
    print_messages: bool = True,
) -> bool:
    """
    Check if a NetCDF file is corrupted.

    Args:
        file_path (str): Path to the NetCDF file.
        delete_if_invalid (bool): Whether to delete the file if it is corrupted. Default is False.
        print_messages (bool): Whether to print messages during the check. Default is True.

    Returns:
        bool: True if the file is valid, False otherwise.

    Example:
        >>> is_valid = check('file.nc', delete_if_invalid=True)
    """
    is_valid = False

    if not os.path.exists(file_path):
        if print_messages:
            print(f"[yellow]File not found: {file_path}[/yellow]")
        return False

    try:
        import netCDF4 as nc
        with nc.Dataset(file_path, "r") as ds_verify:
            if not ds_verify.variables:
                if print_messages:
                    print(f"[red]Empty variables in file: {file_path}[/red]")
            else:
                _ = ds_verify.__dict__
                for var in ds_verify.variables.values():
                    _ = var.shape
                    break
                is_valid = True

    except Exception as e:
        if print_messages:
            print(f"[red]File validation failed: {file_path} - {str(e)}[/red]")

    if not is_valid and delete_if_invalid:
        try:
            os.remove(file_path)
            if print_messages:
                print(f"[red]Deleted corrupted file: {file_path}[/red]")
        except Exception as del_error:
            if print_messages:
                print(f"[red]Failed to delete file: {file_path} - {str(del_error)}[/red]")

    return is_valid


def convert_longitude(
    dataset: xr.Dataset,
    longitude_name: str = "longitude",
    target_range: int = 180,
) -> xr.Dataset:
    """
    Convert the longitude array to a specified range.

    Args:
        dataset (xr.Dataset): The xarray dataset containing the longitude data.
        longitude_name (str): Name of the longitude variable. Default is "longitude".
        target_range (int): Target range to convert to, either 180 or 360. Default is 180.

    Returns:
        xr.Dataset: Dataset with converted longitude.

    Example:
        >>> dataset = convert_longitude(dataset, longitude_name="lon", target_range=360)
    """
    if target_range not in [180, 360]:
        raise ValueError("target_range value must be 180 or 360")

    if target_range == 180:
        dataset = dataset.assign_coords({longitude_name: (dataset[longitude_name] + 180) % 360 - 180})
    else:
        dataset = dataset.assign_coords({longitude_name: (dataset[longitude_name] + 360) % 360})

    return dataset.sortby(longitude_name)


def isel(
    file_path: str,
    dimension_name: str,
    indices: List[int],
) -> xr.Dataset:
    """
    Select data by the index of a dimension.

    Args:
        file_path (str): Path to the NetCDF file.
        dimension_name (str): Name of the dimension.
        indices (List[int]): Indices of the dimension to select.

    Returns:
        xr.Dataset: Subset dataset.

    Example:
        >>> subset = isel('file.nc', 'time', [0, 1, 2])
    """
    ds = xr.open_dataset(file_path)
    indices = [int(i) for i in np.array(indices).flatten()]
    ds_new = ds.isel(**{dimension_name: indices})
    ds.close()
    return ds_new


def draw(
    output_directory: Optional[str] = None,
    dataset: Optional[xr.Dataset] = None,
    file_path: Optional[str] = None,
    dims_xyzt: Union[List[str], Tuple[str, str, str, str]] = None,
    plot_style: str = "contourf",
    use_fixed_colorscale: bool = False,
) -> None:
    """
    Draw data from a NetCDF file.

    Args:
        output_directory (Optional[str]): Path of the output directory.
        dataset (Optional[xr.Dataset]): Xarray dataset to plot.
        file_path (Optional[str]): Path to the NetCDF file.
        dims_xyzt (Union[List[str], Tuple[str, str, str, str]]): Dimensions for plotting. xyzt
        plot_style (str): Type of the plot, e.g., "contourf" or "contour". Default is "contourf".
        use_fixed_colorscale (bool): Whether to use a fixed colorscale. Default is False.

    Example:
        >>> draw(output_directory="plots", file_path="file.nc", plot_style="contour")
    """
    from ._script.plot_dataset import func_plot_dataset

    if output_directory is None:
        output_directory = os.getcwd()
    if not isinstance(dims_xyzt, (list, tuple)) and dims_xyzt is not None:
        raise ValueError("dimensions must be a list or tuple")

    if dataset is not None:
        func_plot_dataset(dataset, output_directory, dims_xyzt, plot_style, use_fixed_colorscale)
    elif file_path is not None:
        if check(file_path):
            ds = xr.open_dataset(file_path)
            func_plot_dataset(ds, output_directory, dims_xyzt, plot_style, use_fixed_colorscale)
        else:
            print(f"[red]Invalid file: {file_path}[/red]")
    else:
        print("[red]No dataset or file provided.[/red]")


def compress(src_path, dst_path=None,convert_dtype='int16'):
    """
    压缩 NetCDF 文件，使用 scale_factor/add_offset 压缩数据。
    若 dst_path 省略，则自动生成新文件名，写出后删除原文件并将新文件改回原名。
    """
    src_path = str(src_path)
    # 判断是否要替换原文件
    delete_orig = dst_path is None
    if delete_orig:
        dst_path = src_path.replace(".nc", "_compress_temp.nc")

    ds = xr.open_dataset(src_path)
    save(dst_path, ds, convert_dtype=convert_dtype, use_scale_offset=True, use_compression=True)
    ds.close()

    if delete_orig:
        os.remove(src_path)
        os.rename(dst_path, src_path)
    pass


def unscale(src_path, dst_path=None, compression_level=4):
    """解码 NetCDF 并移除 scale_factor/add_offset，写出真实值。
    保留压缩功能，但不使用比例因子和偏移量，以控制文件大小。
    若 dst_path 省略，则自动生成新文件名，写出后删除原文件并将新文件改回原名。

    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径，None则替换原文件
        compression_level: 压缩级别(1-9)，数值越大压缩比越高，速度越慢
    """
    src_path = str(src_path)
    # 判断是否要替换原文件
    delete_orig = dst_path is None
    if delete_orig:
        dst_path = src_path.replace(".nc", "_unpacked_temp.nc")

    # 打开原始文件，获取文件大小
    orig_size = os.path.getsize(src_path) / (1024 * 1024)  # MB

    # 先以原始模式打开，查看哪些变量使用了scale_factor/add_offset
    with xr.open_dataset(src_path, decode_cf=False) as ds_raw:
        has_scaling = []
        for var in ds_raw.data_vars:
            if "scale_factor" in ds_raw[var].attrs or "add_offset" in ds_raw[var].attrs:
                has_scaling.append(var)

    print(f"[yellow]文件: {src_path} (原始大小: {orig_size:.2f} MB)[/yellow]")
    if has_scaling:
        print(f"[yellow]发现 {len(has_scaling)} 个变量使用了比例因子: {', '.join(has_scaling)}[/yellow]")
    else:
        print("[yellow]未发现任何变量使用比例因子，解包可能不必要[/yellow]")

    # 解码模式打开
    ds = xr.open_dataset(src_path, decode_cf=True)
    encoding = {}

    for var in ds.data_vars:
        # 保存原始的_FillValue
        fill_value = None
        if "_FillValue" in ds[var].attrs:
            fill_value = ds[var].attrs["_FillValue"]
        elif "_FillValue" in ds[var].encoding:
            fill_value = ds[var].encoding["_FillValue"]

        # 清除scale_factor和add_offset属性
        ds[var].attrs.pop("scale_factor", None)
        ds[var].attrs.pop("add_offset", None)
        ds[var].encoding.clear()

        # 仅对数值型变量处理
        if np.issubdtype(ds[var].dtype, np.number):
            # 强制转换为float32，避免float64导致文件暴涨
            if np.issubdtype(ds[var].dtype, np.floating) and ds[var].dtype != np.float32:
                ds[var] = ds[var].astype(np.float32)

            # 设置压缩参数，但不使用scale_factor/add_offset
            encoding[var] = {"zlib": True, "complevel": compression_level, "dtype": ds[var].dtype}
            # 恢复_FillValue
            if fill_value is not None:
                encoding[var]["_FillValue"] = fill_value

    # 使用save函数保存，传入encoding确保只压缩不使用scale_factor
    ds.to_netcdf(dst_path, encoding=encoding)
    ds.close()

    # 打印输出文件大小对比
    if os.path.exists(dst_path):
        new_size = os.path.getsize(dst_path) / (1024 * 1024)  # MB
        size_change = new_size - orig_size
        change_percent = (size_change / orig_size) * 100

        color = "green" if size_change <= 0 else "red"
        print(f"[{color}]解包后文件大小: {new_size:.2f} MB ({change_percent:+.1f}%)[/{color}]")

        if size_change > orig_size * 0.5 and new_size > 100:  # 如果文件增长超过50%且大于100MB
            print(f"[red]警告: 文件大小增长显著! 考虑增加压缩级别(当前:{compression_level})[/red]")

    if delete_orig:
        os.remove(src_path)
        os.rename(dst_path, src_path)
        print(f"[green]已替换原文件: {src_path}[/green]")
    else:
        print(f"[green]已保存到: {dst_path}[/green]")


if __name__ == "__main__":
    data = np.random.rand(100, 50)
    save(r"test.nc", data, "data", {"time": np.linspace(0, 120, 100), "lev": np.linspace(0, 120, 50)}, "a")
