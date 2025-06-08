import os
import shutil
import psutil
import wmi



def is_ssd(path):
    """
    Attempts to determine if the given path is on an SSD.
    Returns True if SSD, False if HDD, or None if unknown.
    """
    try:
        partition = next(p for p in psutil.disk_partitions(all=False) if path.startswith(p.mountpoint))
        usage = psutil.disk_usage(partition.mountpoint)
        device = partition.device

        # Windows only: use WMI to check for MediaType = 'SSD'
        if os.name == "nt":
            import pythoncom
            import wmi

            pythoncom.CoInitialize()  # ✅ FIX: Required in threads

            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                if device in disk.DeviceID:
                    return 'ssd' in disk.MediaType.lower()

    except Exception as e:
        print(f"⚠️ Could not determine disk type: {e}")
    return None


def move_file(file_path, target_folder):
    """
    Move a single file (image or text) to the target folder.
    """
    try:
        if not os.path.exists(target_folder):
            os.makedirs(target_folder, exist_ok=True)

        file_name = os.path.basename(file_path)
        destination = os.path.join(target_folder, file_name)
        shutil.move(file_path, destination)
        return True
    except Exception as e:
        print(f"Error moving {file_path} → {target_folder}: {e}")
        return False

def move_files(file_paths, target_folder, threads='auto', verbose=False, pbar=None):
    """
    Move multiple files to the target folder using threads.

    :param file_paths: List of full paths to files
    :param target_folder: Destination folder
    :param threads: Number of worker threads. Use "auto" to auto-detect based on drive type (8 for SSD, 3 for HDD).
                    You can also set a specific integer. If an invalid value is given, a safe default is used.
    :param verbose: Whether to print progress info
    :param pbar: Optional tqdm progress bar instance to update as files are moved
    """
    import concurrent.futures
    import multiprocessing

    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)

    # Determine threads
    if threads == 'auto':
        threads = 8 if is_ssd(target_folder) else 3
    else:
        try:
            threads = int(threads)
        except (ValueError, TypeError):
            print(f"⚠️ Invalid thread count: '{threads}'. Falling back to safe default (4 threads).")
            threads = 4

    # ✅ Enforce system-safe limits
    max_threads = multiprocessing.cpu_count() * 2
    threads = max(1, min(threads, max_threads))

    def safe_move(src):
        try:
            move_file(src, target_folder)
            if verbose:
                print(f"✅ Moved: {src}")
            if pbar:
                pbar.update(1)
        except Exception as e:
            print(f"❌ Failed to move {src}: {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(safe_move, file_paths)
