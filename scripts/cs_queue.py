import shutil
import time
from filelock import FileLock, Timeout
import os
from send2trash import send2trash

class QueueManager:
    def __init__(self, lock_file="file_operations_log.lock", log_file="file_operations_log.yaml", timeout=5):
        self.lock_file = lock_file
        self.log_file = log_file
        self.timeout = timeout
        self.queue = []

    def add_to_queue(self, src, dst):
        """Add file to the processing queue."""
        self.queue.append({"src": src, "dst": dst, "attempts": 0})

    def process_queue(self):
        """Process the queue."""
        for item in list(self.queue):  # Iterate over a copy of the queue
            src = item["src"]
            dst = item["dst"]
            attempts = item["attempts"]

            if attempts >= 3:
                print(f"Max retries reached for {src}. Skipping...")
                self.queue.remove(item)
                continue

            try:
                # Hash-checking logic
                if os.path.exists(dst):
                    source_hash = self.calculate_file_hash(src)
                    destination_hash = self.calculate_file_hash(dst)
                    if source_hash == destination_hash:
                        print(f"File {src} already exists in destination and is identical. Skipping.")
                        self.queue.remove(item)
                        continue
                    else:
                        print(f"File {src} is different from {dst}. Renaming.")
                        base, ext = os.path.splitext(dst)
                        dst = f"{base}_new{ext}"

                # Move or copy the file
                shutil.move(src, dst)
                print(f"Moved {src} to {dst}")
                self.queue.remove(item)
            except PermissionError as e:
                print(f"PermissionError: {e}. Retrying in 2 seconds...")
                item["attempts"] += 1
            except Exception as e:
                print(f"Error processing {src}: {e}")
                self.queue.remove(item)

    def cleanup_lock_file(self):
        """Cleanup the lock file after processing."""
        if os.path.exists(self.lock_file):
            try:
                send2trash(self.lock_file)
                print(f"Cleaned up lock file: {self.lock_file}")
            except Exception as e:
                print(f"Error cleaning up lock file: {e}")
                
    @staticmethod
    def calculate_file_hash(file_path, block_size=65536):
        """Calculate the SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(block_size):
                    sha256.update(chunk)
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None
        return sha256.hexdigest()
