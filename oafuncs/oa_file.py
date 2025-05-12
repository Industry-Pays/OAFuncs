import glob
import os
import re
import shutil
from typing import Dict, List, Optional, Union

from rich import print

__all__ = ["find_file", "link_file", "copy_file", "rename_file", "move_file", "clear_folder", "remove_empty_folder", "remove", "file_size", "mean_size", "make_dir", "replace_content"]


def find_file(parent_dir: Union[str, os.PathLike], file_pattern: str, return_mode: str = "path") -> List[str]:
    """Finds files matching a specified pattern.

    Args:
        parent_dir: The parent directory where to search for files
        file_pattern: The file name pattern to search for
        return_mode: Return mode, 'path' to return full file paths, 'file' to return only file names. Defaults to 'path'

    Returns:
        A list of file paths or file names if files are found, otherwise an empty list
    """

    def natural_sort_key(s: str) -> List[Union[int, str]]:
        """Generate a key for natural sorting."""
        return [int(text) if text.isdigit() else text.lower() for text in re.split("([0-9]+)", s)]

    search_pattern = os.path.join(str(parent_dir), file_pattern)
    matched_files = glob.glob(search_pattern)

    if not matched_files:
        return []

    matched_files = sorted(matched_files, key=natural_sort_key)

    if return_mode == "file":
        result = [os.path.basename(file) for file in matched_files]
    else:
        result = [os.path.abspath(file) for file in matched_files]

    return result


def link_file(source_pattern: str, destination: str) -> None:
    """Creates symbolic links with wildcard support.

    Args:
        source_pattern: Source file or directory pattern (supports wildcards)
        destination: Destination file or directory

    Examples:
        >>> link_file(r'/data/hejx/liukun/era5/*', r'/data/hejx/liukun/Test/')
        >>> link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
        >>> link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test')
    """
    source_pattern = str(source_pattern)
    src_files = glob.glob(source_pattern) if "*" in source_pattern else [source_pattern]

    if not src_files:
        print(f"[yellow]No matching files or directories found for:[/yellow] '[bold]{source_pattern}[/bold]'")
        return

    for src_file in src_files:
        try:
            if os.path.isdir(destination):
                dst_file = os.path.join(destination, os.path.basename(src_file))
            else:
                dst_file = destination

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            if os.path.exists(dst_file):
                os.remove(dst_file)
            os.symlink(src_file, dst_file)

            print(f"[green]Successfully created symbolic link:[/green] [bold]{src_file}[/bold] -> [bold]{dst_file}[/bold]")
        except Exception as e:
            print(f"[red]Failed to create symbolic link:[/red] [bold]{src_file}[/bold]. Error: {e}")


def copy_file(source_pattern: str, destination: str) -> None:
    """Copies files or directories with wildcard support.

    Args:
        source_pattern: Source file or directory pattern (supports wildcards)
        destination: Destination file or directory

    Examples:
        >>> copy_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
        >>> copy_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test')
    """
    source_pattern = str(source_pattern)
    src_files = glob.glob(source_pattern) if "*" in source_pattern else [source_pattern]

    if not src_files:
        print(f"[yellow]No matching files or directories found for:[/yellow] '[bold]{source_pattern}[/bold]'")
        return

    for src_file in src_files:
        try:
            if os.path.isdir(destination):
                dst_file = os.path.join(destination, os.path.basename(src_file))
            else:
                dst_file = destination

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            if os.path.exists(dst_file):
                if os.path.isdir(dst_file):
                    shutil.rmtree(dst_file)
                else:
                    os.remove(dst_file)

            if os.path.isdir(src_file):
                shutil.copytree(src_file, dst_file, symlinks=True)
            else:
                shutil.copy2(src_file, dst_file)

            print(f"[green]Successfully copied:[/green] [bold]{src_file}[/bold] -> [bold]{dst_file}[/bold]")
        except Exception as e:
            print(f"[red]Failed to copy:[/red] [bold]{src_file}[/bold]. Error: {e}")


def move_file(source_pattern: str, destination: str) -> None:
    """Moves files or directories with wildcard support.

    Args:
        source_pattern: Source file or directory pattern (supports wildcards)
        destination: Destination file or directory

    Examples:
        >>> move_file(r'/data/hejx/liukun/era5/*', r'/data/hejx/liukun/Test/')
        >>> move_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
        >>> move_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test')
    """
    source_pattern = str(source_pattern)
    src_files = glob.glob(source_pattern) if "*" in source_pattern else [source_pattern]

    if not src_files:
        print(f"[yellow]No matching files or directories found for:[/yellow] '[bold]{source_pattern}[/bold]'")
        return

    for src_file in src_files:
        try:
            if os.path.isdir(destination):
                dst_file = os.path.join(destination, os.path.basename(src_file))
            else:
                dst_file = destination

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            if os.path.exists(dst_file):
                if os.path.isdir(dst_file):
                    shutil.rmtree(dst_file)
                else:
                    os.remove(dst_file)
            shutil.move(src_file, dst_file)

            print(f"[green]Successfully moved:[/green] [bold]{src_file}[/bold] -> [bold]{dst_file}[/bold]")
        except Exception as e:
            print(f"[red]Failed to move:[/red] [bold]{src_file}[/bold]. Error: {e}")


def rename_file(target_dir: str, old_substring: str, new_substring: str) -> None:
    """Renames files in a directory by replacing specified string patterns.

    Recursively processes all files in the directory, replacing parts of filenames
    that contain the specified string.

    Args:
        target_dir: The directory path to process
        old_substring: The string to be replaced
        new_substring: The new string to replace with

    Examples:
        >>> directory_path = r"E:\\windfarm\\CROCO_FILES"
        >>> old_substring = "croco"
        >>> new_substring = "roms"
        >>> rename_file(directory_path, old_substring, new_substring)
    """
    for root, _, files in os.walk(target_dir):
        pattern = re.compile(re.escape(old_substring))

        for filename in files:
            if pattern.search(filename):
                new_filename = pattern.sub(new_substring, filename)
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)
                os.rename(old_path, new_path)
                print(f"[green]Rename file:[/green] [bold]{old_path}[/bold] -> [bold]{new_path}[/bold]")


def make_dir(target_dir: Union[str, os.PathLike]) -> None:
    """Creates a directory if it does not exist.

    Args:
        target_dir: The directory path to create

    Examples:
        >>> make_dir(r"E:\\Data\\2024\\09\\17\\var1")
    """
    target_dir = str(target_dir)
    if os.path.exists(target_dir):
        print(f"[blue]Directory already exists:[/blue] [bold]{target_dir}[/bold]")
        return
    else:
        os.makedirs(target_dir, exist_ok=True)
        print(f"[green]Created directory:[/green] [bold]{target_dir}[/bold]")


def clear_folder(target_folder: Union[str, os.PathLike]) -> None:
    """Clears all contents of the specified folder.

    Removes all files and subdirectories within the folder, while preserving the folder itself.

    Args:
        target_folder: Path of the folder to clear

    Examples:
        >>> clear_folder(r'E:\\Data\\2024\\09\\17\\var1')
    """
    target_folder = str(target_folder)
    if os.path.exists(target_folder):
        try:
            for filename in os.listdir(target_folder):
                file_path = os.path.join(target_folder, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print(f"[green]Successfully cleared the folder:[/green] [bold]{target_folder}[/bold]")
        except Exception as e:
            print(f"[red]Failed to clear the folder:[/red] [bold]{target_folder}[/bold]")
            print(f"[red]{e}[/red]")


def remove_empty_folder(target_path: Union[str, os.PathLike], verbose: int = 1) -> None:
    """Recursively removes all empty folders under the specified path.

    Args:
        target_path: The folder path to process
        verbose: Whether to print processing information, 1 means print, 0 means no print

    Examples:
        >>> remove_empty_folder(r'E:\\Data\\2024\\09\\17', verbose=1)
    """
    target_path = str(target_path)
    for root, dirs, files in os.walk(target_path, topdown=False):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            try:
                os.listdir(folder_path)
            except OSError:
                continue
            if not os.listdir(folder_path):
                try:
                    os.rmdir(folder_path)
                    print(f"[green]Deleted empty folder:[/green] [bold]{folder_path}[/bold]")
                except OSError:
                    if verbose:
                        print(f"[yellow]Skipping protected folder:[/yellow] [bold]{folder_path}[/bold]")
                    pass


def remove(target_pattern: str) -> None:
    """Deletes files or directories that match the given wildcard pattern.

    Args:
        target_pattern: File path or string containing wildcards

    Examples:
        >>> remove(r'E:\\Code\\Python\\Model\\WRF\\Radar2\\bzip2-radar-0*')
        >>> # or, assuming you are already in the target directory
        >>> # os.chdir(r'E:\\Code\\Python\\Model\\WRF\\Radar2')
        >>> # remove('bzip2-radar-0*')
    """
    target_pattern = str(target_pattern)
    file_list = glob.glob(target_pattern) if "*" in target_pattern else [target_pattern]

    if not file_list:
        print(f"[yellow]No matching files or directories found for:[/yellow] '[bold]{target_pattern}[/bold]'")
        return

    for file_path in file_list:
        try:
            if os.path.isdir(file_path) or os.path.isfile(file_path) or os.path.islink(file_path):
                (shutil.rmtree if os.path.isdir(file_path) else os.remove)(file_path)
                print(f"[green]Successfully deleted:[/green] [bold]{file_path}[/bold]")
            else:
                if not os.path.exists(file_path):
                    # print(f"[yellow]File not found:[/yellow] [bold]{file_path}[/bold]")
                    pass
                else:
                    print(f"[yellow]Skipping unknown file type:[/yellow] [bold]{file_path}[/bold]")
        except Exception as e:
            print(f"[red]Failed to delete:[/red] [bold]{file_path}[/bold]. Error: {e}")


def file_size(file_path: Union[str, os.PathLike], unit: str = "KB", verbose: bool = False) -> float:
    """Gets the size of a file in the specified unit.

    Args:
        file_path: Path to the file
        unit: Size unit, can be PB, TB, GB, MB, KB, or B
        verbose: Whether to display information about the file size

    Returns:
        The file size in the specified unit, or 0.0 if file doesn't exist or unit is invalid

    Examples:
        >>> size = file_size("myfile.txt", "MB")
        >>> print(f"File size is {size} MB")
    """
    unit = unit.upper()
    unit_dict = {"PB": 1024**5, "TB": 1024**4, "GB": 1024**3, "MB": 1024**2, "KB": 1024, "B": 1}

    if unit not in unit_dict:
        if verbose:
            print("[yellow]Invalid unit, please choose one of PB, TB, GB, MB, KB, B[/yellow]")
        return 0.0

    if not os.path.isfile(file_path):
        if verbose:
            print(f"[yellow]Invalid file path or not a file:[/yellow] [bold]{file_path}[/bold]")
        return 0.0

    try:
        size_in_bytes = os.path.getsize(file_path)
        size = size_in_bytes / unit_dict[unit]
        if verbose:
            print(f"[green]File size:[/green] [bold]{size:.2f} {unit}[/bold]")
        return size
    except (OSError, IOError) as e:
        if verbose:
            print(f"[red]Error getting file size:[/red] {e}")
        return 0.0


def mean_size(parent_dir: Union[str, os.PathLike], file_pattern: str, max_files: Optional[int] = None, unit: str = "KB") -> float:
    """Calculates the average size of specified files in a folder.

    Args:
        parent_dir: The parent directory where the files are located
        file_pattern: The file name pattern to search for
        max_files: Maximum number of files to process, process all matching files if None
        unit: File size unit, defaults to "KB"

    Returns:
        Average file size. Returns 0.0 if no files are found or all files have size 0

    Examples:
        >>> avg_size = mean_size("/data/logs", "*.log", max_files=10, unit="MB")
        >>> print(f"Average log file size is {avg_size} MB")
    """
    # 获取文件列表
    flist = find_file(parent_dir, file_pattern)
    if not flist:
        print(f"[yellow]No files found matching pattern:[/yellow] [bold]{file_pattern}[/bold] in [bold]{parent_dir}[/bold]")
        return 0.0

    # 处理最大文件数限制
    if max_files is not None:
        try:
            max_files = int(max_files)
            if max_files > 0:
                flist = flist[:max_files]
            else:
                print("[yellow]max_files must be positive, using all files[/yellow]")
        except (ValueError, TypeError):
            print(f"[yellow]Invalid max_files value:[/yellow] [bold]{max_files}[/bold], using all files")

    # 获取每个文件的大小并过滤掉大小为0的文件
    size_list = [file_size(f, unit) for f in flist]
    valid_sizes = [size for size in size_list if size > 0]

    # 计算平均值
    if valid_sizes:
        avg_size = sum(valid_sizes) / len(valid_sizes)
        if len(valid_sizes) < len(size_list):
            print(f"[blue]Note:[/blue] {len(size_list) - len(valid_sizes)} files were skipped (size 0 or error)")
        return avg_size
    else:
        print("[yellow]No valid files with size > 0 found[/yellow]")
        return 0.0


def replace_content(source_file: Union[str, os.PathLike], replacements: Dict[str, str], use_key_value: bool = False, target_dir: Optional[Union[str, os.PathLike]] = None, new_filename: Optional[str] = None) -> None:
    """Directly replaces specified content in a file and saves to a new path.

    Args:
        source_file: Path to the source file
        replacements: Dictionary of content to replace {old_content: new_content}
        use_key_value: Whether to replace parameters as key-value pairs
        target_dir: Target directory path, uses the source file's directory if None
        new_filename: New file name, keeps the original file name if None

    Examples:
        >>> replace_content("config.txt", {"old_value": "new_value"})
        >>> replace_content("template.xml", {"name": "John", "age": "30"}, use_key_value=True)
    """
    from ._script.replace_file_content import replace_direct_content

    if target_dir is None:
        target_dir = os.path.dirname(source_file)
    replace_direct_content(source_file, target_dir, replacements, key_value=use_key_value, new_name=new_filename)


if __name__ == "__main__":
    pass

    remove(r"I:\\Delete\\test\\*")
