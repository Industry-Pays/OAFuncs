import os
import warnings

import netCDF4 as nc
import numpy as np
import xarray as xr

warnings.filterwarnings("ignore", category=RuntimeWarning)



def _nan_to_fillvalue(ncfile,set_fill_value):
    """
    将 NetCDF 文件中所有变量的 NaN 和掩码值替换为其 _FillValue 属性（若无则自动添加 _FillValue=-32767 并替换）。
    同时处理掩码数组中的无效值。
    仅对数值型变量（浮点型、整型）生效。
    """
    with nc.Dataset(ncfile, "r+") as ds:
        for var_name in ds.variables:
            var = ds.variables[var_name]
            # 只处理数值类型变量 (f:浮点型, i:有符号整型, u:无符号整型)
            if var.dtype.kind not in ["f", "i", "u"]:
                continue

            # 读取数据
            arr = var[:]

            # 确定填充值
            if "_FillValue" in var.ncattrs():
                fill_value = var.getncattr("_FillValue")
            elif hasattr(var, "missing_value"):
                fill_value = var.getncattr("missing_value")
            else:
                fill_value = set_fill_value
                try:
                    var.setncattr("_FillValue", fill_value)
                except Exception:
                    # 某些变量可能不允许动态添加 _FillValue
                    continue

            # 处理掩码数组
            if hasattr(arr, "mask"):
                # 如果是掩码数组，将掩码位置的值设为 fill_value
                if np.any(arr.mask):
                    arr = np.where(arr.mask, fill_value, arr.data if hasattr(arr, "data") else arr)

            # 处理剩余 NaN 和无穷值
            if arr.dtype.kind in ["f", "i", "u"] and np.any(~np.isfinite(arr)):
                arr = np.nan_to_num(arr, nan=fill_value, posinf=fill_value, neginf=fill_value)

            # 写回变量
            var[:] = arr


def _numpy_to_nc_type(numpy_type):
    """将 NumPy 数据类型映射到 NetCDF 数据类型"""
    numpy_to_nc = {
        "float32": "f4",
        "float64": "f8",
        "int8": "i1",
        "int16": "i2",
        "int32": "i4",
        "int64": "i8",
        "uint8": "u1",
        "uint16": "u2",
        "uint32": "u4",
        "uint64": "u8",
    }
    numpy_type_str = str(numpy_type) if not isinstance(numpy_type, str) else numpy_type
    return numpy_to_nc.get(numpy_type_str, "f4")


def _calculate_scale_and_offset(data, dtype="int32"):
    """
    只对有效数据（非NaN、非填充值、非自定义缺失值）计算scale_factor和add_offset。
    使用 int32 类型，n=32
    """
    if not isinstance(data, np.ndarray):
        raise ValueError("Input data must be a NumPy array.")
    
    if dtype == "int32":
        n = 32
        fill_value = np.iinfo(np.int32).min  # -2147483648
    elif dtype == "int16":
        n = 16
        fill_value = np.iinfo(np.int16).min  # -32768
    else:
        raise ValueError("Unsupported dtype. Supported types are 'int16' and 'int32'.")

    # 有效掩码：非NaN、非inf、非fill_value
    valid_mask = np.isfinite(data) & (data != fill_value)
    if hasattr(data, "mask") and np.ma.is_masked(data):
        valid_mask &= ~data.mask

    if np.any(valid_mask):
        data_min = np.min(data[valid_mask])-1
        data_max = np.max(data[valid_mask])+1
    else:
        data_min, data_max = 0, 1

    # 防止scale为0，且保证scale/offset不会影响缺省值
    if data_max == data_min:
        scale_factor = 1.0
        add_offset = data_min
    else:
        scale_factor = (data_max - data_min) / (2**n - 2)
        add_offset = (data_max + data_min) / 2.0
    return scale_factor, add_offset


def _data_to_scale_offset(data, scale, offset, dtype='int32'):
    """
    只对有效数据做缩放，NaN/inf/填充值直接赋为fill_value。
    掩码区域的值会被保留并进行缩放，除非掩码本身标记为无效。
    使用 int32 类型
    """
    if not isinstance(data, np.ndarray):
        raise ValueError("Input data must be a NumPy array.")
    
    if dtype == "int32":
        # n = 32
        np_dtype = np.int32
        fill_value = np.iinfo(np.int32).min  # -2147483648
        clip_min = np.iinfo(np.int32).min + 1  # -2147483647
        clip_max = np.iinfo(np.int32).max  # 2147483647
    elif dtype == "int16":
        # n = 16
        np_dtype = np.int16
        fill_value = np.iinfo(np.int16).min  # -32768
        clip_min = np.iinfo(np.int16).min + 1  # -32767
        clip_max = np.iinfo(np.int16).max  # 32767
    else:
        raise ValueError("Unsupported dtype. Supported types are 'int16' and 'int32'.")

    # 创建掩码，只排除 NaN/inf 和显式的填充值
    valid_mask = np.isfinite(data)
    valid_mask &= data != fill_value

    # 如果数据有掩码属性，还需考虑掩码
    if hasattr(data, "mask") and np.ma.is_masked(data):
        # 只有掩码标记的区域视为无效
        valid_mask &= ~data.mask

    result = data.copy()
    if np.any(valid_mask):
        # 反向映射时能还原原始值
        scaled = (data[valid_mask] - offset) / scale
        scaled = np.round(scaled).astype(np_dtype)
        # clip到int32范围，保留最大范围供转换
        scaled = np.clip(scaled, clip_min, clip_max)  # 不使用 -2147483648，保留做 _FillValue
        result[valid_mask] = scaled
    return result


def save_to_nc(file, data, varname=None, coords=None, mode="w", convert_dtype='int32',scale_offset_switch=True, compile_switch=True, preserve_mask_values=True):
    """
    保存数据到 NetCDF 文件，支持 xarray 对象（DataArray 或 Dataset）和 numpy 数组。

    仅对数据变量中数值型数据进行压缩转换（利用 scale_factor/add_offset 转换后转为 int32），
    非数值型数据以及所有坐标变量将禁用任何压缩，直接保存原始数据。

    参数：
      - file: 保存文件的路径
      - data: xarray.DataArray、xarray.Dataset 或 numpy 数组
      - varname: 变量名（仅适用于传入 numpy 数组或 DataArray 时）
      - coords: 坐标字典（numpy 数组分支时使用），所有坐标变量均不压缩
      - mode: "w"（覆盖）或 "a"（追加）
      - convert_dtype: 转换为的数值类型（"int16" 或 "int32"），默认为 "int32"
      - scale_offset_switch: 是否对数值型数据变量进行压缩转换
      - compile_switch: 是否启用 NetCDF4 的 zlib 压缩（仅针对数值型数据有效）
      - missing_value: 自定义缺失值，将被替换为 fill_value
      - preserve_mask_values: 是否保留掩码区域的原始值（True）或将其替换为缺省值（False）
    """
    if convert_dtype not in ["int16", "int32"]:
        convert_dtype = "int32"
    nc_dtype = _numpy_to_nc_type(convert_dtype)
    # fill_value = np.iinfo(np.convert_dtype).min  # -2147483648 或 -32768
    # fill_value = np.iinfo(eval('np.' + convert_dtype)).min  # -2147483648 或 -32768
    np_dtype = getattr(np, convert_dtype)  # 更安全的类型获取方式
    fill_value = np.iinfo(np_dtype).min
    # ----------------------------------------------------------------------------
    # 处理 xarray 对象（DataArray 或 Dataset）的情况
    if isinstance(data, (xr.DataArray, xr.Dataset)):
        encoding = {}

        if isinstance(data, xr.DataArray):
            if data.name is None:
                data = data.rename("data")
            varname = data.name if varname is None else varname
            arr = np.array(data.values)
            try:
                data_missing_val = data.attrs.get("missing_value")
            except AttributeError:
                data_missing_val = data.attrs.get("_FillValue", None)
            # 只对有效数据计算scale/offset
            valid_mask = np.ones(arr.shape, dtype=bool)  # 默认所有值都有效
            if arr.dtype.kind in ["f", "i", "u"]:  # 仅对数值数据应用isfinite
                valid_mask = np.isfinite(arr)
                if data_missing_val is not None:
                    valid_mask &= arr != data_missing_val
                if hasattr(arr, "mask"):
                    valid_mask &= ~getattr(arr, "mask", False)
            if np.issubdtype(arr.dtype, np.number) and scale_offset_switch:
                arr_valid = arr[valid_mask]
                scale, offset = _calculate_scale_and_offset(arr_valid, convert_dtype)
                # 写入前处理无效值（只在这里做！）
                arr_to_save = arr.copy()
                # 处理自定义缺失值
                if data_missing_val is not None:
                    arr_to_save[arr == data_missing_val] = fill_value
                # 处理 NaN/inf
                arr_to_save[~np.isfinite(arr_to_save)] = fill_value
                new_values = _data_to_scale_offset(arr_to_save, scale, offset)
                new_da = data.copy(data=new_values)
                # 移除 _FillValue 和 missing_value 属性
                for k in ["_FillValue", "missing_value"]:
                    if k in new_da.attrs:
                        del new_da.attrs[k]
                new_da.attrs["scale_factor"] = float(scale)
                new_da.attrs["add_offset"] = float(offset)
                encoding[varname] = {
                    "zlib": compile_switch,
                    "complevel": 4,
                    "dtype": nc_dtype,
                    # "_FillValue": -2147483648,
                }
                new_da.to_dataset(name=varname).to_netcdf(file, mode=mode, encoding=encoding)
            else:
                for k in ["_FillValue", "missing_value"]:
                    if k in data.attrs:
                        del data.attrs[k]
                data.to_dataset(name=varname).to_netcdf(file, mode=mode)
            _nan_to_fillvalue(file, fill_value)
            return

        else:  # Dataset 情况
            new_vars = {}
            encoding = {}
            for var in data.data_vars:
                da = data[var]
                arr = np.array(da.values)
                try:
                    data_missing_val = da.attrs.get("missing_value")
                except AttributeError:
                    data_missing_val = da.attrs.get("_FillValue", None)
                valid_mask = np.ones(arr.shape, dtype=bool)  # 默认所有值都有效
                if arr.dtype.kind in ["f", "i", "u"]:  # 仅对数值数据应用isfinite
                    valid_mask = np.isfinite(arr)
                    if data_missing_val is not None:
                        valid_mask &= arr != data_missing_val
                    if hasattr(arr, "mask"):
                        valid_mask &= ~getattr(arr, "mask", False)

                # 创建属性的副本以避免修改原始数据集
                attrs = da.attrs.copy()
                for k in ["_FillValue", "missing_value"]:
                    if k in attrs:
                        del attrs[k]

                if np.issubdtype(arr.dtype, np.number) and scale_offset_switch:
                    # 处理边缘情况：检查是否有有效数据
                    if not np.any(valid_mask):
                        # 如果没有有效数据，创建一个简单的拷贝，不做转换
                        new_vars[var] = xr.DataArray(arr, dims=da.dims, coords=da.coords, attrs=attrs)
                        continue

                    arr_valid = arr[valid_mask]
                    scale, offset = _calculate_scale_and_offset(arr_valid, convert_dtype)
                    arr_to_save = arr.copy()

                    # 使用与DataArray相同的逻辑，使用_data_to_scale_offset处理数据
                    # 处理自定义缺失值
                    if data_missing_val is not None:
                        arr_to_save[arr == data_missing_val] = fill_value
                    # 处理 NaN/inf
                    arr_to_save[~np.isfinite(arr_to_save)] = fill_value
                    new_values = _data_to_scale_offset(arr_to_save, scale, offset)
                    new_da = xr.DataArray(new_values, dims=da.dims, coords=da.coords, attrs=attrs)
                    new_da.attrs["scale_factor"] = float(scale)
                    new_da.attrs["add_offset"] = float(offset)
                    # 不设置_FillValue属性，改为使用missing_value
                    # new_da.attrs["missing_value"] = -2147483648
                    new_vars[var] = new_da
                    encoding[var] = {
                        "zlib": compile_switch,
                        "complevel": 4,
                        "dtype": nc_dtype,
                    }
                else:
                    new_vars[var] = xr.DataArray(arr, dims=da.dims, coords=da.coords, attrs=attrs)

            # 确保坐标变量被正确复制
            new_ds = xr.Dataset(new_vars, coords=data.coords.copy())
            new_ds.to_netcdf(file, mode=mode, encoding=encoding if encoding else None)
        _nan_to_fillvalue(file, fill_value)
        return

    # 处理纯 numpy 数组情况
    if mode == "w" and os.path.exists(file):
        os.remove(file)
    elif mode == "a" and not os.path.exists(file):
        mode = "w"
    data = np.asarray(data)
    is_numeric = np.issubdtype(data.dtype, np.number)

    if hasattr(data, "mask") and np.ma.is_masked(data):
        # 处理掩码数组，获取缺失值
        data = data.data
        missing_value = getattr(data, "missing_value", None)
    else:
        missing_value = None
    
    try:
        with nc.Dataset(file, mode, format="NETCDF4") as ncfile:
            if coords is not None:
                for dim, values in coords.items():
                    if dim not in ncfile.dimensions:
                        ncfile.createDimension(dim, len(values))
                        var_obj = ncfile.createVariable(dim, _numpy_to_nc_type(np.asarray(values).dtype), (dim,))
                        var_obj[:] = values

            dims = list(coords.keys()) if coords else []
            if is_numeric and scale_offset_switch:
                arr = np.array(data)

                # 构建有效掩码，但不排除掩码区域的数值（如果 preserve_mask_values 为 True）
                valid_mask = np.isfinite(arr)  # 排除 NaN 和无限值
                if missing_value is not None:
                    valid_mask &= arr != missing_value  # 排除明确的缺失值

                # 如果不保留掩码区域的值，则将掩码区域视为无效
                if not preserve_mask_values and hasattr(arr, "mask"):
                    valid_mask &= ~arr.mask

                arr_to_save = arr.copy()

                # 确保有有效数据
                if not np.any(valid_mask):
                    # 如果没有有效数据，不进行压缩，直接保存原始数据类型
                    dtype = _numpy_to_nc_type(data.dtype)
                    var = ncfile.createVariable(varname, dtype, dims, zlib=False)
                    # 确保没有 NaN
                    clean_data = np.nan_to_num(data, nan=missing_value if missing_value is not None else fill_value)
                    var[:] = clean_data
                    return

                # 计算 scale 和 offset 仅使用有效区域数据
                arr_valid = arr_to_save[valid_mask]
                scale, offset = _calculate_scale_and_offset(arr_valid, convert_dtype)

                # 执行压缩转换
                new_data = _data_to_scale_offset(arr_to_save, scale, offset)

                # 创建变量并设置属性
                var = ncfile.createVariable(varname, nc_dtype, dims, zlib=compile_switch)
                var.scale_factor = scale
                var.add_offset = offset
                var._FillValue = fill_value  # 明确设置填充值
                var[:] = new_data
            else:
                dtype = _numpy_to_nc_type(data.dtype)
                var = ncfile.createVariable(varname, dtype, dims, zlib=False)
                # 确保不写入 NaN
                if np.issubdtype(data.dtype, np.floating) and np.any(~np.isfinite(data)):
                    fill_val = missing_value if missing_value is not None else fill_value
                    var._FillValue = fill_val
                    clean_data = np.nan_to_num(data, nan=fill_val)
                    var[:] = clean_data
                else:
                    var[:] = data
        # 最后确保所有 NaN 值被处理
        _nan_to_fillvalue(file, fill_value)
    except Exception as e:
        raise RuntimeError(f"netCDF4 保存失败: {str(e)}") from e


def _compress_netcdf(src_path, dst_path=None, tolerance=1e-10, preserve_mask_values=True):
    """
    压缩 NetCDF 文件，使用 scale_factor/add_offset 压缩数据。
    若 dst_path 省略，则自动生成新文件名，写出后删除原文件并将新文件改回原名。
    压缩后验证数据是否失真。

    参数：
      - src_path: 原始 NetCDF 文件路径
      - dst_path: 压缩后的文件路径（可选）
      - tolerance: 数据验证的允许误差范围（默认 1e-10）
      - preserve_mask_values: 是否保留掩码区域的原始值（True）或将其替换为缺省值（False）
    """
    # 判断是否要替换原文件
    delete_orig = dst_path is None
    if delete_orig:
        dst_path = src_path.replace(".nc", "_compress.nc")
    # 打开原始文件并保存压缩文件
    ds = xr.open_dataset(src_path)
    save_to_nc(dst_path, ds, convert_dtype='int32',scale_offset_switch=True, compile_switch=True, preserve_mask_values=preserve_mask_values)
    ds.close()

    # 验证压缩后的数据是否失真
    original_ds = xr.open_dataset(src_path)
    compressed_ds = xr.open_dataset(dst_path)
    # 更详细地验证数据
    for var in original_ds.data_vars:
        original_data = original_ds[var].values
        compressed_data = compressed_ds[var].values
        # 跳过非数值类型变量
        if not np.issubdtype(original_data.dtype, np.number):
            continue
        # 获取掩码（如果存在）
        original_mask = None
        if hasattr(original_data, "mask") and np.ma.is_masked(original_data):  # 修正：确保是有效的掩码数组
            original_mask = original_data.mask.copy()
        # 检查有效数据是否在允许误差范围内
        valid_mask = np.isfinite(original_data)
        if original_mask is not None:
            valid_mask &= ~original_mask
        if np.any(valid_mask):
            if np.issubdtype(original_data.dtype, np.floating):
                diff = np.abs(original_data[valid_mask] - compressed_data[valid_mask])
                max_diff = np.max(diff)
                if max_diff > tolerance:
                    print(f"警告: 变量 {var} 的压缩误差 {max_diff} 超出容许范围 {tolerance}")
                    if max_diff > tolerance * 10:  # 严重偏差时抛出错误
                        raise ValueError(f"变量 {var} 的数据在压缩后严重失真 (max_diff={max_diff})")
            elif np.issubdtype(original_data.dtype, np.integer):
                # 整数类型应该完全相等
                if not np.array_equal(original_data[valid_mask], compressed_data[valid_mask]):
                    raise ValueError(f"变量 {var} 的整数数据在压缩后不一致")
        # 如果需要保留掩码区域值，检查掩码区域的值
        if preserve_mask_values and original_mask is not None and np.any(original_mask):
            # 确保掩码区域的原始值被正确保留
            # 修正：掩码数组可能存在数据类型不匹配问题，添加安全检查
            try:
                mask_diff = np.abs(original_data[original_mask] - compressed_data[original_mask])
                if np.any(mask_diff > tolerance):
                    print(f"警告: 变量 {var} 的掩码区域数据在压缩后发生变化")
            except Exception as e:
                print(f"警告: 变量 {var} 的掩码区域数据比较失败: {str(e)}")
    original_ds.close()
    compressed_ds.close()

    # 替换原文件
    if delete_orig:
        os.remove(src_path)
        os.rename(dst_path, src_path)


# 测试用例
if __name__ == "__main__":
    # 示例文件路径，需根据实际情况修改
    file = "dataset_test.nc"
    ds = xr.open_dataset(file)
    outfile = "dataset_test_compressed.nc"
    save_to_nc(outfile, ds)
    ds.close()

    # dataarray
    data = np.random.rand(4, 3, 2)
    coords = {"x": np.arange(4), "y": np.arange(3), "z": np.arange(2)}
    varname = "test_var"
    data = xr.DataArray(data, dims=("x", "y", "z"), coords=coords, name=varname)
    outfile = "test_dataarray.nc"
    save_to_nc(outfile, data)

    # numpy array with custom missing value
    coords = {"dim0": np.arange(5)}
    data = np.array([1, 2, -999, 4, np.nan])
    save_to_nc("test_numpy_missing.nc", data, varname="data", coords=coords, missing_value=-999)
