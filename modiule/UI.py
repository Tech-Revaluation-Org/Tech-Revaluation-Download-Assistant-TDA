import os
import sys
import asyncio
import httpx
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QDialog, QCheckBox, QHBoxLayout, QStyle, QFormLayout
from urllib.parse import urlsplit
import mimetypes
from plyer import notification

# Global variable for mute status
mute_notifications = False

# Default settings
settings = {
    'num_connections': 20,
    'package_size': 1024 * 1024,  # 1MB chunk size
    'use_threads': False,
    'num_threads': 4
}

# Function to download a chunk of the file
async def download_chunk(client, url, start_byte, end_byte, download_path, filename, progress_callback, speed_callback):
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        part_filename = os.path.join(download_path, f"{filename}_part{start_byte}-{end_byte}")
        
        with open(part_filename, 'ab') as file:  # Use 'ab' to append to the existing file
            total_bytes_downloaded = 0
            async for chunk in response.aiter_bytes(1024):  # Use aiter_bytes() to read in chunks asynchronously
                if not chunk:
                    break
                file.write(chunk)
                total_bytes_downloaded += len(chunk)
                progress_callback(len(chunk))  # Update progress
                speed_callback(total_bytes_downloaded)  # Update speed
        print(f"Downloaded part {part_filename}")
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error downloading chunk: {e}")

# Function to download the file in multiple connections
async def multi_connection_download(url, download_path, filename, num_connections=4, pkg_size=1024 * 1024, use_threads=False, num_threads=4, progress_callback=None, speed_callback=None):
    os.makedirs(download_path, exist_ok=True)
    
    # Get the file size
    async with httpx.AsyncClient() as client:
        response = await client.head(url)
        file_size = int(response.headers['Content-Length'])
        chunk_size = min(file_size // num_connections, pkg_size)

        tasks = []
        start_bytes = [i * chunk_size for i in range(num_connections)]
        end_bytes = [
            (i + 1) * chunk_size - 1 if i != num_connections - 1 else file_size - 1
            for i in range(num_connections)
        ]

        # Check for existing parts and adjust download range
        for i in range(num_connections):
            part_filename = os.path.join(download_path, f"{filename}_part{start_bytes[i]}-{end_bytes[i]}")
            if os.path.exists(part_filename):
                with open(part_filename, 'rb') as part_file:
                    if len(part_file.read()) == end_bytes[i] - start_bytes[i] + 1:
                        continue  # Skip downloading this part if it's complete
                    else:
                        start_bytes[i] = os.path.getsize(part_filename)

        # Download in multiple chunks
        for i in range(num_connections):
            task = asyncio.create_task(
                download_chunk(client, url, start_bytes[i], end_bytes[i], download_path, filename, progress_callback, speed_callback))
            tasks.append(task)

        await asyncio.gather(*tasks)

    # Combine downloaded parts into one complete file
    with open(os.path.join(download_path, filename), 'wb') as output_file:
        for i in range(num_connections):
            part_filename = os.path.join(download_path, f"{filename}_part{start_bytes[i]}-{end_bytes[i]}")
            
            # Check if the part file exists before attempting to read
            if os.path.exists(part_filename):
                with open(part_filename, 'rb') as part_file:
                    output_file.write(part_file.read())
                os.remove(part_filename)  # Remove the part file after merging
            else:
                print(f"Part file {part_filename} is missing!")
                
    print(f"Download completed: {filename}")

# Function to extract filename from URL
def extract_filename_from_url(url):
    base_filename = os.path.basename(urlsplit(url).path)
    
    if not base_filename:
        base_filename = url.split('/')[-1] or "downloaded_file"
    
    mime_type, _ = mimetypes.guess_type(base_filename)
    if not mime_type:
        return base_filename

    extension = mime_type.split('/')[1]
    if '.' not in base_filename:
        base_filename += f".{extension}"

    return base_filename

# Worker thread for downloading
class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    speed = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, url, download_path, filename, num_connections, pkg_size, use_threads, num_threads):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.filename = filename
        self.num_connections = num_connections
        self.pkg_size = pkg_size
        self.use_threads = use_threads
        self.num_threads = num_threads

    def run(self):
        asyncio.run(multi_connection_download(self.url, self.download_path, self.filename, self.num_connections, self.pkg_size, self.use_threads, self.num_threads, self.progress.emit, self.speed.emit))
        self.finished.emit()

# GUI part with PyQt6
class DownloadManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Download Manager")
        self.setGeometry(300, 300, 500, 400)
        
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter URL to download...")

        self.download_button = QPushButton("Start Download", self)
        self.download_button.clicked.connect(self.toggle_download)

        self.speed_label = QLabel("Speed: 0 KB/s", self)
        self.time_remaining_label = QLabel("Time Remaining: 0 seconds", self)

        self.mute_button = QPushButton(self)
        self.mute_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.mute_button.clicked.connect(self.toggle_mute)

        self.settings_button = QPushButton(self)
        self.settings_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.settings_button.clicked.connect(self.open_settings)

        self.folder_label = QLabel("Download Folder: None", self)
        self.select_folder_button = QPushButton("Choose Download Folder", self)
        self.select_folder_button.clicked.connect(self.select_folder)

        # Form layout for settings
        self.settings_layout = QFormLayout()
        self.num_connections_input = QSpinBox(self)
        self.num_connections_input.setValue(settings['num_connections'])
        self.settings_layout.addRow("Num Connections", self.num_connections_input)

        self.package_size_input = QSpinBox(self)
        self.package_size_input.setValue(settings['package_size'] // (1024 * 1024))  # in MB
        self.settings_layout.addRow("Package Size (MB)", self.package_size_input)

        self.use_threads_checkbox = QCheckBox("Use Threads", self)
        self.use_threads_checkbox.setChecked(settings['use_threads'])
        self.settings_layout.addRow("Use Threads", self.use_threads_checkbox)

        self.num_threads_input = QSpinBox(self)
        self.num_threads_input.setValue(settings['num_threads'])
        self.settings_layout.addRow("Num Threads", self.num_threads_input)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.url_input)
        self.layout.addWidget(self.download_button)
        self.layout.addWidget(self.speed_label)
        self.layout.addWidget(self.time_remaining_label)
        self.layout.addWidget(self.mute_button)
        self.layout.addWidget(self.settings_button)
        self.layout.addWidget(self.folder_label)
        self.layout.addWidget(self.select_folder_button)
        self.layout.addLayout(self.settings_layout)
        
        central_widget = QWidget(self)
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.current_folder = ""  # Set to a default path later
        self.download_worker = None

        # Timer to update the speed every second
        self.speed_timer = QTimer(self)
        self.speed_timer.timeout.connect(self.update_network_speed)
        self.downloaded_bytes = 0  # Store downloaded bytes to calculate speed
        self.last_update_time = 0  # Time for the last update to calculate time differences

    def toggle_download(self):
        url = self.url_input.text()
        if self.download_button.text() == "Start Download":
            self.download_button.setText("Stop Download")
            filename = extract_filename_from_url(url)
            download_path = self.current_folder
            num_connections = self.num_connections_input.value()
            package_size = self.package_size_input.value() * 1024 * 1024  # Convert MB to bytes
            use_threads = self.use_threads_checkbox.isChecked()
            num_threads = self.num_threads_input.value()

            self.download_worker = DownloadWorker(url, download_path, filename, num_connections, package_size, use_threads, num_threads)
            self.download_worker.progress.connect(self.update_speed)
            self.download_worker.speed.connect(self.update_speed_real_time)
            self.download_worker.finished.connect(self.download_finished)
            self.download_worker.start()
            
            # Start the speed timer to update speed every second
            self.speed_timer.start(1000)
        else:
            self.download_button.setText("Start Download")
            if self.download_worker:
                self.download_worker.terminate()  # Stop the download if it's running
            self.speed_timer.stop()  # Stop the speed timer

    def download_finished(self):
        self.download_button.setText("Start Download")
        if not mute_notifications:
            notification.notify(title="Download Complete", message="Your download is complete.")

    def update_speed(self, bytes_downloaded):
        # Update downloaded bytes
        self.downloaded_bytes += bytes_downloaded

    def update_network_speed(self):
        # Calculate speed (bytes per second)
        current_time = asyncio.get_event_loop().time()
        elapsed_time = current_time - self.last_update_time

        if elapsed_time >= 1:  # Update every second
            speed = self.downloaded_bytes / elapsed_time / 1024  # in KB/s
            self.speed_label.setText(f"Speed: {speed:.2f} KB/s")

            self.last_update_time = current_time
            self.downloaded_bytes = 0  # Reset the counter

    def update_speed_real_time(self, total_downloaded_bytes):
        self.downloaded_bytes = total_downloaded_bytes

    def toggle_mute(self):
        global mute_notifications
        mute_notifications = not mute_notifications
        icon = QStyle.StandardPixmap.SP_MediaVolumeMuted if mute_notifications else QStyle.StandardPixmap.SP_MediaVolume
        self.mute_button.setIcon(self.style().standardIcon(icon))

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.current_folder = folder
            self.folder_label.setText(f"Download Folder: {folder}")

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(400, 400, 300, 200)
        self.layout = QVBoxLayout(self)
        
        self.num_connections_input = QSpinBox(self)
        self.num_connections_input.setValue(settings['num_connections'])
        self.layout.addWidget(self.num_connections_input)
        
        self.package_size_input = QSpinBox(self)
        self.package_size_input.setValue(settings['package_size'] // (1024 * 1024))  # MB
        self.layout.addWidget(self.package_size_input)

        self.use_threads_checkbox = QCheckBox(self)
        self.use_threads_checkbox.setChecked(settings['use_threads'])
        self.layout.addWidget(self.use_threads_checkbox)

        self.num_threads_input = QSpinBox(self)
        self.num_threads_input.setValue(settings['num_threads'])
        self.layout.addWidget(self.num_threads_input)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

    def save_settings(self):
        settings['num_connections'] = self.num_connections_input.value()
        settings['package_size'] = self.package_size_input.value() * 1024 * 1024  # Convert MB to bytes
        settings['use_threads'] = self.use_threads_checkbox.isChecked()
        settings['num_threads'] = self.num_threads_input.value()
        self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DownloadManager()
    window.show()
    sys.exit(app.exec())
