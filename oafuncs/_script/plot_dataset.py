import os
from typing import Optional, Tuple, Union

import matplotlib as mpl

mpl.use("Agg")  # Use non-interactive backend

import cartopy.crs as ccrs
import cftime
import matplotlib.pyplot as plt
import numpy as np
import oafuncs
import xarray as xr
from rich import print


def plot_1d(data: xr.DataArray, output_path: str, x_dim: str, y_dim: str, z_dim: str, t_dim: str) -> None:
    """Plot 1D data."""
    plt.figure(figsize=(10, 6))

    # Handle time dimension
    if t_dim in data.dims and isinstance(data[t_dim].values[0], cftime.datetime):
        try:
            data[t_dim] = data.indexes[t_dim].to_datetimeindex()
        except (AttributeError, ValueError, TypeError) as e:
            print(f"Warning: Could not convert {t_dim} to datetime index: {e}")

    # Determine X axis data
    x, x_label = determine_x_axis(data, x_dim, y_dim, z_dim, t_dim)

    y = data.values
    plt.plot(x, y, linewidth=2)

    # Add chart info
    long_name = getattr(data, "long_name", "No long_name")
    units = getattr(data, "units", "")
    plt.title(f"{data.name} | {long_name}", fontsize=12)
    plt.xlabel(x_label)
    plt.ylabel(f"{data.name} ({units})" if units else data.name)

    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    # Save image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=600)
    plt.clf()
    plt.close()


def determine_x_axis(data: xr.DataArray, x_dim: str, y_dim: str, z_dim: str, t_dim: str) -> Tuple[np.ndarray, str]:
    """Determine the X axis data and label."""
    if x_dim in data.dims:
        return data[x_dim].values, x_dim
    elif y_dim in data.dims:
        return data[y_dim].values, y_dim
    elif z_dim in data.dims:
        return data[z_dim].values, z_dim
    elif t_dim in data.dims:
        return data[t_dim].values, t_dim
    else:
        return np.arange(len(data)), "Index"


def plot_2d(data: xr.DataArray, output_path: str, data_range: Optional[Tuple[float, float]], x_dim: str, y_dim: str, t_dim: str, plot_type: str) -> bool:
    """Plot 2D data."""
    if x_dim in data.dims and y_dim in data.dims and x_dim.lower() in ["lon", "longitude"] and y_dim.lower() in ["lat", "latitude"]:
        lon_range = data[x_dim].values
        lat_range = data[y_dim].values
        lon_lat_ratio = np.abs(np.max(lon_range) - np.min(lon_range)) / (np.max(lat_range) - np.min(lat_range))
        figsize = (10, 10 / lon_lat_ratio)
        fig, ax = plt.subplots(figsize=figsize, subplot_kw={"projection": ccrs.PlateCarree()})
        oafuncs.oa_draw.add_cartopy(ax, lon_range, lat_range)
    else:
        fig, ax = plt.subplots(figsize=(10, 8))

    # Handle time dimension
    if t_dim in data.dims and isinstance(data[t_dim].values[0], cftime.datetime):
        try:
            data[t_dim] = data.indexes[t_dim].to_datetimeindex()
        except (AttributeError, ValueError, TypeError) as e:
            print(f"Warning: Could not convert {t_dim} to datetime index: {e}")

    # Check for valid data
    if np.all(np.isnan(data.values)) or data.size == 0:
        print(f"Skipping {data.name}: All values are NaN or empty")
        plt.close()
        return False

    data_range = calculate_data_range(data, data_range)

    if data_range is None:
        print(f"Skipping {data.name} due to all NaN values")
        plt.close()
        return False

    # Select appropriate colormap and levels
    cmap, norm, levels = select_colormap_and_levels(data_range, plot_type)

    mappable = None
    try:
        if plot_type == "contourf":
            if np.ptp(data.values) < 1e-10 and not np.all(np.isnan(data.values)):
                print(f"Warning: {data.name} has very little variation. Using imshow instead.")
                mappable = ax.imshow(data.values, cmap=cmap, aspect="auto", interpolation="none")
                colorbar = plt.colorbar(mappable, ax=ax)
            else:
                mappable = ax.contourf(data[x_dim], data[y_dim], data.values, levels=levels, cmap=cmap, norm=norm)
                colorbar = plt.colorbar(mappable, ax=ax)
        elif plot_type == "contour":
            if np.ptp(data.values) < 1e-10 and not np.all(np.isnan(data.values)):
                print(f"Warning: {data.name} has very little variation. Using imshow instead.")
                mappable = ax.imshow(data.values, cmap=cmap, aspect="auto", interpolation="none")
                colorbar = plt.colorbar(mappable, ax=ax)
            else:
                mappable = ax.contour(data[x_dim], data[y_dim], data.values, levels=levels, cmap=cmap, norm=norm)
                ax.clabel(mappable, inline=True, fontsize=8, fmt="%1.1f")
                colorbar = plt.colorbar(mappable, ax=ax)
    except (ValueError, TypeError) as e:
        print(f"Warning: Could not plot with specified parameters: {e}. Trying simplified parameters.")
        try:
            mappable = data.plot(ax=ax, cmap=cmap, add_colorbar=False)
            colorbar = plt.colorbar(mappable, ax=ax)
        except Exception as e2:
            print(f"Error plotting {data.name}: {e2}")
            plt.figure(figsize=(10, 8))
            mappable = ax.imshow(data.values, cmap="viridis", aspect="auto")
            colorbar = plt.colorbar(mappable, ax=ax, label=getattr(data, "units", ""))
            plt.title(f"{data.name} | {getattr(data, 'long_name', 'No long_name')} (basic plot)", fontsize=12)
            plt.tight_layout()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, bbox_inches="tight", dpi=600)
            plt.close()
            return True

    plt.title(f"{data.name} | {getattr(data, 'long_name', 'No long_name')}", fontsize=12)
    units = getattr(data, "units", "")
    if units and colorbar:
        colorbar.set_label(units)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=600)
    plt.close()
    return True


def calculate_data_range(data: xr.DataArray, data_range: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """Calculate the data range, ignoring extreme outliers."""
    if data_range is None:
        flat_data = data.values.flatten()
        if flat_data.size == 0:
            return None
        valid_data = flat_data[~np.isnan(flat_data)]
        if len(valid_data) == 0:
            return None
        low, high = np.percentile(valid_data, [0.5, 99.5])
        filtered_data = valid_data[(valid_data >= low) & (valid_data <= high)]
        if len(filtered_data) > 0:
            data_range = (np.min(filtered_data), np.max(filtered_data))
        else:
            data_range = (np.nanmin(valid_data), np.nanmax(valid_data))
        if abs(data_range[1] - data_range[0]) < 1e-10:
            mean = (data_range[0] + data_range[1]) / 2
            data_range = (mean - 1e-10 if mean != 0 else -1e-10, mean + 1e-10 if mean != 0 else 1e-10)
    return data_range


def select_colormap_and_levels(data_range: Tuple[float, float], plot_type: str) -> Tuple[mpl.colors.Colormap, mpl.colors.Normalize, np.ndarray]:
    """Select colormap and levels based on data range."""
    if plot_type == "contour":
        # For contour plots, use fewer levels
        num_levels = 10
    else:
        # For filled contour plots, use more levels
        num_levels = 128

    if data_range[0] * data_range[1] < 0:
        cmap = oafuncs.oa_cmap.get("diverging_1")
        bdy = max(abs(data_range[0]), abs(data_range[1]))
        norm = mpl.colors.TwoSlopeNorm(vmin=-bdy, vcenter=0, vmax=bdy)
        levels = np.linspace(-bdy, bdy, num_levels)
    else:
        cmap = oafuncs.oa_cmap.get("cool_1") if data_range[0] < 0 else oafuncs.oa_cmap.get("warm_1")
        norm = mpl.colors.Normalize(vmin=data_range[0], vmax=data_range[1])
        levels = np.linspace(data_range[0], data_range[1], num_levels)

    if np.any(np.diff(levels) <= 0):
        levels = np.linspace(data_range[0], data_range[1], 10)
    return cmap, norm, levels


def process_variable(var: str, data: xr.DataArray, dims: int, dims_name: Tuple[str, ...], output_dir: str, x_dim: str, y_dim: str, z_dim: str, t_dim: str, fixed_colorscale: bool, plot_type: str) -> None:
    """Process a single variable."""
    valid_dims = {x_dim, y_dim, z_dim, t_dim}
    if not set(dims_name).issubset(valid_dims):
        print(f"Skipping {var} due to unsupported dimensions: {dims_name}")
        return

    # Process 1D data
    if dims == 1:
        if np.issubdtype(data.dtype, np.character):
            print(f"Skipping {var} due to character data type")
            return
        plot_1d(data, os.path.join(output_dir, f"{var}.png"), x_dim, y_dim, z_dim, t_dim)
        print(f"{var}.png")
        return

    # Compute global data range for fixed colorscale
    global_data_range = None
    if dims >= 2 and fixed_colorscale:
        global_data_range = calculate_data_range(data, None)
        if global_data_range is None:
            print(f"Skipping {var} due to no valid data")
            return
        print(f"Fixed colorscale range: {global_data_range}")

    # Process 2D data
    if dims == 2:
        success = plot_2d(data, os.path.join(output_dir, f"{var}.png"), global_data_range, x_dim, y_dim, t_dim, plot_type)
        if success:
            print(f"{var}.png")

    # Process 3D data
    if dims == 3:
        for i in range(data.shape[0]):
            for attempt in range(10):
                try:
                    if data[i].values.size == 0:
                        print(f"Skipped {var}_{dims_name[0]}-{i} (empty data)")
                        break
                    success = plot_2d(data[i], os.path.join(output_dir, f"{var}_{dims_name[0]}-{i}.png"), global_data_range, x_dim, y_dim, t_dim, plot_type)
                    if success:
                        print(f"{var}_{dims_name[0]}-{i}.png")
                    else:
                        print(f"Skipped {var}_{dims_name[0]}-{i} (invalid data)")
                    break
                except Exception as e:
                    if attempt < 9:
                        print(f"Retrying {var}_{dims_name[0]}-{i} (attempt {attempt + 1})")
                    else:
                        print(f"Error processing {var}_{dims_name[0]}-{i}: {e}")

    # Process 4D data
    if dims == 4:
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                for attempt in range(3):
                    try:
                        if data[i, j].values.size == 0:
                            print(f"Skipped {var}_{dims_name[0]}-{i}_{dims_name[1]}-{j} (empty data)")
                            break
                        success = plot_2d(data[i, j], os.path.join(output_dir, f"{var}_{dims_name[0]}-{i}_{dims_name[1]}-{j}.png"), global_data_range, x_dim, y_dim, t_dim, plot_type)
                        if success:
                            print(f"{var}_{dims_name[0]}-{i}_{dims_name[1]}-{j}.png")
                        else:
                            print(f"Skipped {var}_{dims_name[0]}-{i}_{dims_name[1]}-{j} (invalid data)")
                        break
                    except Exception as e:
                        if attempt < 2:
                            print(f"Retrying {var}_{dims_name[0]}-{i}_{dims_name[1]}-{j} (attempt {attempt + 1})")
                        else:
                            print(f"Error processing {var}_{dims_name[0]}-{i}_{dims_name[1]}-{j}: {e}")


def func_plot_dataset(ds_in: Union[xr.Dataset, xr.DataArray], output_dir: str, xyzt_dims: Tuple[str, str, str, str] = ("longitude", "latitude", "level", "time"), plot_type: str = "contourf", fixed_colorscale: bool = False) -> None:
    """Plot variables from a NetCDF file and save the plots to the specified directory."""
    os.makedirs(output_dir, exist_ok=True)
    x_dim, y_dim, z_dim, t_dim = xyzt_dims

    # Main processing function
    try:
        # 检查输入是 DataArray 还是 Dataset
        if isinstance(ds_in, xr.DataArray):
            # 处理单个 DataArray
            print("Processing a single DataArray")
            var = ds_in.name if ds_in.name is not None else "unnamed_variable"
            print("=" * 120)
            print(f"Processing: {var}")
            try:
                dims = len(ds_in.shape)
                dims_name = ds_in.dims
                process_variable(var, ds_in, dims, dims_name, output_dir, x_dim, y_dim, z_dim, t_dim, fixed_colorscale, plot_type)
            except Exception as e:
                print(f"Error processing variable {var}: {e}")
        else:
            # 处理包含多个变量的 Dataset
            ds = ds_in
            varlist = list(ds.data_vars)
            print(f"Found {len(varlist)} variables in dataset")

            for var in varlist:
                print("=" * 120)
                print(f"Processing: {var}")
                data = ds[var]
                dims = len(data.shape)
                dims_name = data.dims
                try:
                    process_variable(var, data, dims, dims_name, output_dir, x_dim, y_dim, z_dim, t_dim, fixed_colorscale, plot_type)
                except Exception as e:
                    print(f"Error processing variable {var}: {e}")

    except Exception as e:
        print(f"Error processing dataset: {e}")
    finally:
        if isinstance(ds_in, xr.Dataset) and "ds_in" in locals():
            ds_in.close()
            print("Dataset closed")


if __name__ == "__main__":
    pass
    # func_plot_dataset(ds, output_dir, xyzt_dims=("longitude", "latitude", "level", "time"), plot_type="contourf", fixed_colorscale=False)
