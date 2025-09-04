import os
import warnings
import numpy as np
import xarray as xr
import netCDF4 as nc

warnings.filterwarnings("ignore", category=RuntimeWarning)

def _get_dtype_info(dtype):
    """
    根据输入的 dtype 返回其 numpy_type, clip_min, clip_max。
    支持 int8, int16, int32, int64 四种整数类型。
    简化处理：不使用fill_value，所有特殊值统一为NaN。
    使用完整的数据类型范围，不预留填充值空间。
    """
    dtype_map = {
        "int8": (np.int8, np.iinfo(np.int8).min, np.iinfo(np.int8).max),
        "int16": (np.int16, np.iinfo(np.int16).min, np.iinfo(np.int16).max),
        "int32": (np.int32, np.iinfo(np.int32).min, np.iinfo(np.int32).max),
        "int64": (np.int64, np.iinfo(np.int64).min, np.iinfo(np.int64).max),
    }
    if dtype not in dtype_map:
        raise ValueError(f"Unsupported dtype: {dtype}. Supported types are 'int8', 'int16', 'int32', and 'int64'.")
    
    return dtype_map[dtype]


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
    只对有效数据（非NaN、非无穷值、非自定义缺失值）计算scale_factor和add_offset。
    为填充值保留最小值位置，有效数据范围为 [clip_min+1, clip_max]。
    """
    if not isinstance(data, np.ndarray):
        raise ValueError("Input data must be a NumPy array.")

    np_dtype, clip_min, clip_max = _get_dtype_info(dtype)

    # 创建有效数据掩码，只排除NaN和无穷值
    valid_mask = np.isfinite(data)
    if hasattr(data, "mask") and np.ma.is_masked(data):
        valid_mask &= ~data.mask

    # 如果没有有效数据，返回默认值
    if not np.any(valid_mask):
        return 1.0, 0.0

    # 基于有效数据计算最小值和最大值
    data_min = np.min(data[valid_mask])
    data_max = np.max(data[valid_mask])

    # 防止 scale 为 0
    if data_max == data_min:
        scale_factor = 1.0
        add_offset = data_min
    else:
        # 使用数据中心点作为offset
        add_offset = (data_max + data_min) / 2.0
        
        # 计算数据范围相对于中心点的最大偏移
        max_deviation = max(abs(data_max - add_offset), abs(data_min - add_offset))
        
        # 可用的整数范围（为填充值保留最小值）
        available_range = min(abs(clip_min + 1), abs(clip_max))
        scale_factor = max_deviation / available_range

    return scale_factor, add_offset


def _data_to_scale_offset(data, scale, offset, dtype="int32"):
    """
    将数据应用 scale 和 offset 转换，转换为整型以实现压缩。
    NaN、inf 和掩码值将被转换为指定数据类型的最小值作为填充值。
    
    转换公式：scaled_value = (original_value - add_offset) / scale_factor
    返回整型数组，用最小值表示无效数据
    """
    if not isinstance(data, np.ndarray):
        raise ValueError("Input data must be a NumPy array.")

    np_dtype, clip_min, clip_max = _get_dtype_info(dtype)
    fill_value = clip_min  # 使用数据类型的最小值作为填充值
    
    # 创建输出数组，初始化为填充值
    result = np.full(data.shape, fill_value, dtype=np_dtype)
    
    # 只对有限值进行转换
    valid_mask = np.isfinite(data)
    
    # 对于掩码数组，排除掩码区域
    if hasattr(data, "mask") and np.ma.is_masked(data):
        valid_mask &= ~data.mask
    
    if np.any(valid_mask):
        # 进行scale/offset转换
        scaled = (data[valid_mask] - offset) / scale
        # 四舍五入并转换为目标整型，同时确保在有效范围内
        scaled_int = np.round(scaled).astype(np_dtype)
        # 由于我们使用了最小值作为填充值，所以有效数据范围是 [clip_min+1, clip_max]
        scaled_int = np.clip(scaled_int, clip_min + 1, clip_max)
        result[valid_mask] = scaled_int
    
    return result, fill_value


def save_to_nc(file, data, varname=None, coords=None, mode="w", convert_dtype='int16', scale_offset_switch=True, compile_switch=True, preserve_mask_values=True, missing_value=None):
    """
    保存数据到 NetCDF 文件，支持 xarray 对象（DataArray 或 Dataset）和 numpy 数组。

    仅对数据变量中数值型数据进行压缩转换（利用 scale_factor/add_offset 转换后转为指定整数类型），
    非数值型数据以及所有坐标变量将禁用任何压缩，直接保存原始数据。
    
    简化处理：所有特殊值（missing_value、掩码、无穷值等）统一转换为NaN处理。

    参数：
      - file: 保存文件的路径
      - data: xarray.DataArray、xarray.Dataset 或 numpy 数组
      - varname: 变量名（仅适用于传入 numpy 数组或 DataArray 时）
      - coords: 坐标字典（numpy 数组分支时使用），所有坐标变量均不压缩
      - mode: "w"（覆盖）或 "a"（追加）
      - convert_dtype: 转换为的数值类型（"int8", "int16", "int32", "int64"），默认为 "int32"
      - scale_offset_switch: 是否对数值型数据变量进行压缩转换
      - compile_switch: 是否启用 NetCDF4 的 zlib 压缩（仅针对数值型数据有效）
      - preserve_mask_values: 是否保留掩码区域的原始值（True）或将其替换为缺省值（False）
      - missing_value: 自定义缺失值，将被替换为 NaN
    """
    if convert_dtype not in ["int8", "int16", "int32", "int64"]:
        convert_dtype = "int32"
    nc_dtype = _numpy_to_nc_type(convert_dtype)

    # ----------------------------------------------------------------------------
    # 处理 xarray 对象（DataArray 或 Dataset）
    if isinstance(data, (xr.DataArray, xr.Dataset)):
        encoding = {}
        if isinstance(data, xr.DataArray):
            if data.name is None:
                data = data.rename("data")
            varname = data.name if varname is None else varname
            arr = np.array(data.values)
            data_missing_val = data.attrs.get("missing_value", None)

            valid_mask = np.ones(arr.shape, dtype=bool)
            if arr.dtype.kind in ["f", "i", "u"]:
                valid_mask = np.isfinite(arr)
                if data_missing_val is not None:
                    valid_mask &= arr != data_missing_val
                if hasattr(arr, "mask"):
                    valid_mask &= ~arr.mask

            if np.issubdtype(arr.dtype, np.number) and scale_offset_switch:
                # 确保有有效数据用于计算scale/offset
                if not np.any(valid_mask):
                    # 如果没有有效数据，不进行压缩转换
                    for k in ["_FillValue", "missing_value"]:
                        if k in data.attrs:
                            del data.attrs[k]
                    data.to_dataset(name=varname).to_netcdf(file, mode=mode)
                    return

                arr_valid = arr[valid_mask]
                scale, offset = _calculate_scale_and_offset(arr_valid, convert_dtype)

                # 创建需要转换的数据副本，但不修改特殊值
                arr_to_save = arr.copy()
                
                # 只处理自定义缺失值，转换为NaN（让后面统一处理）
                if data_missing_val is not None:
                    arr_to_save[arr == data_missing_val] = np.nan

                # 进行压缩转换（_data_to_scale_offset会正确处理NaN和掩码）
                new_values, fill_value = _data_to_scale_offset(arr_to_save, scale, offset, convert_dtype)
                new_da = data.copy(data=new_values)
                
                # 清除原有的填充值属性，设置新的压缩属性
                for k in ["_FillValue", "missing_value"]:
                    if k in new_da.attrs:
                        del new_da.attrs[k]
                        
                new_da.attrs["scale_factor"] = float(scale)
                new_da.attrs["add_offset"] = float(offset)
                
                encoding[varname] = {
                    "zlib": compile_switch,
                    "complevel": 4,
                    "dtype": nc_dtype,
                    "_FillValue": fill_value,  # 使用计算出的填充值
                }
                new_da.to_dataset(name=varname).to_netcdf(file, mode=mode, encoding=encoding)
            else:
                # 对于非数值数据或不压缩的情况，移除填充值属性防止冲突
                for k in ["_FillValue", "missing_value"]:
                    if k in data.attrs:
                        del data.attrs[k]
                data.to_dataset(name=varname).to_netcdf(file, mode=mode)
            return

        else:  # Dataset 情况
            new_vars = {}
            encoding = {}
            for var in data.data_vars:
                da = data[var]
                arr = np.array(da.values)
                data_missing_val = da.attrs.get("missing_value", None)

                valid_mask = np.ones(arr.shape, dtype=bool)
                if arr.dtype.kind in ["f", "i", "u"]:
                    valid_mask = np.isfinite(arr)
                    if data_missing_val is not None:
                        valid_mask &= arr != data_missing_val
                    if hasattr(arr, "mask"):
                        valid_mask &= ~arr.mask

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

                    # 只处理自定义缺失值，转换为NaN（让后面统一处理）
                    if data_missing_val is not None:
                        arr_to_save[arr == data_missing_val] = np.nan
                    
                    # 进行压缩转换（_data_to_scale_offset会正确处理NaN和掩码）
                    new_values, fill_value = _data_to_scale_offset(arr_to_save, scale, offset, convert_dtype)
                    new_da = xr.DataArray(new_values, dims=da.dims, coords=da.coords, attrs=attrs)
                    new_da.attrs["scale_factor"] = float(scale)
                    new_da.attrs["add_offset"] = float(offset)
                    new_vars[var] = new_da
                    encoding[var] = {
                        "zlib": compile_switch,
                        "complevel": 4,
                        "dtype": nc_dtype,
                        "_FillValue": fill_value,  # 使用计算出的填充值
                    }
                else:
                    new_vars[var] = xr.DataArray(arr, dims=da.dims, coords=da.coords, attrs=attrs)

            # 确保坐标变量被正确复制
            new_ds = xr.Dataset(new_vars, coords=data.coords.copy())
            new_ds.to_netcdf(file, mode=mode, encoding=encoding if encoding else None)
        return

    # 处理纯 numpy 数组情况
    if mode == "w" and os.path.exists(file):
        os.remove(file)
    elif mode == "a" and not os.path.exists(file):
        mode = "w"
    data = np.asarray(data)
    is_numeric = np.issubdtype(data.dtype, np.number)

    # 处理缺失值
    if hasattr(data, "mask") and np.ma.is_masked(data):
        # 处理掩码数组，获取缺失值
        data = data.data
        if missing_value is None:
            missing_value = getattr(data, "missing_value", None)
    
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
                    # 确保没有 NaN，直接用0替换
                    clean_data = np.nan_to_num(data, nan=0.0)
                    var[:] = clean_data
                    return                # 计算 scale 和 offset 仅使用有效区域数据
                arr_valid = arr_to_save[valid_mask]
                scale, offset = _calculate_scale_and_offset(arr_valid, convert_dtype)

                # 只处理自定义缺失值，转换为NaN
                if missing_value is not None:
                    arr_to_save[arr == missing_value] = np.nan

                # 执行压缩转换（_data_to_scale_offset会正确处理NaN和掩码）
                new_data, fill_value = _data_to_scale_offset(arr_to_save, scale, offset, convert_dtype)

                # 创建变量并设置属性
                var = ncfile.createVariable(varname, nc_dtype, dims, zlib=compile_switch, fill_value=fill_value)
                var.scale_factor = scale
                var.add_offset = offset
                var[:] = new_data
            else:
                # 非压缩情况，直接保存但要处理特殊值
                dtype = _numpy_to_nc_type(data.dtype)
                
                clean_data = data.copy()
                
                # 处理自定义缺失值（转换为NaN）
                if missing_value is not None:
                    clean_data[data == missing_value] = np.nan
                
                # 对于整数类型，处理NaN和无穷值 - 用0替换
                if not np.issubdtype(data.dtype, np.floating):
                    finite_mask = np.isfinite(clean_data)
                    if not np.all(finite_mask):
                        clean_data = clean_data.astype(float)  # 转换为浮点型保持NaN
                
                # 处理掩码（统一转换为NaN）
                if hasattr(data, "mask") and np.ma.is_masked(data):
                    clean_data[data.mask] = np.nan
                
                # 创建变量
                var = ncfile.createVariable(varname, dtype, dims, zlib=False)
                var[:] = clean_data
        # 只对压缩数据调用_nan_to_fillvalue，处理掩码但保持NaN
        if is_numeric and scale_offset_switch:
            pass  # 简化策略：不再需要后处理
    except Exception as e:
        raise RuntimeError(f"netCDF4 保存失败: {str(e)}") from e




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
