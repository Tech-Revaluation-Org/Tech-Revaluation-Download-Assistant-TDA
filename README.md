# TRA download more faster 
# Download Manager

This is a simple Python-based download manager with multi-connection support. It allows users to download files from URLs using multiple connections, track download progress, and adjust settings like the number of connections and chunk size. The interface is built using PyQt6 and allows real-time updates on download speed.

## Features

- **Multi-connection download support**: Uses multiple connections to download files faster.
- **Download speed tracking**: Displays download speed in real-time.
- **Folder selection**: Allows users to choose a custom folder for downloads.
- **Settings customization**: Modify settings such as the number of connections, chunk size, and thread usage.
- **Mute notifications**: Option to mute notifications when the download completes.
- **Graphical User Interface (GUI)**: Built using PyQt6, the interface is easy to use and intuitive.

## Requirements

- Python 3.6 or higher
- PyQt6
- `plyer` for desktop notifications

### Install dependencies

Before running the project, install the necessary dependencies using `pip`:

```bash
pip install pyqt6 plyer
