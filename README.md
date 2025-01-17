

# TRA Download Manager

## Overview

**TRA Download Manager** is a powerful and easy-to-use Python-based download manager that optimizes download speeds by utilizing multiple connections. It allows users to efficiently download files from URLs, track download progress in real-time, and adjust settings such as the number of connections and chunk size. The application features a sleek and intuitive graphical user interface (GUI) built with PyQt6, providing a seamless user experience.

### Key Features:

- **Multi-Connection Download**: Download files faster by using multiple connections to split the file into chunks.
- **Real-Time Speed Tracking**: Monitor the current download speed live on the interface.
- **Custom Folder Selection**: Choose any folder to save your downloaded files.
- **Customizable Settings**: Modify important parameters such as the number of connections, chunk size, and thread usage for optimal performance.
- **Mute Notifications**: Option to mute desktop notifications when downloads are completed.
- **Graphical User Interface (GUI)**: Designed with PyQt6 for a modern, user-friendly experience.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.6 or higher**
- **PyQt6**: A set of Python bindings for Qt libraries, which is used to create the GUI.
- **plyer**: For sending desktop notifications when the download is complete.

## Installation

Follow these steps to get your environment set up:

1. **Clone the repository** (if applicable) or navigate to the project directory.
2. **Install the necessary dependencies** using `pip` by running the following command:

    ```bash
    pip install -r requirements.txt
    ```

    This will automatically install all the required packages listed in the `requirements.txt` file.

    **Note**: If you do not have a `requirements.txt` file, you can create one with the following content:

    ```
    pyqt6
    plyer
    httpx
    aiohttp
    mimetypes
    ```

    You can generate this file with:

    ```bash
    pip freeze > requirements.txt
    ```

## Directory Structure

Your project should look like this:

```
your_project_folder/
├── modiule/
│   └── UI.py         # The UI logic of the application
├── main.py           # The entry point to run the application
└── requirements.txt  # The file with all required dependencies
```

## Running the Project

Once all dependencies are installed, run the application by executing the `main.py` file:

```bash
python main.py
```

If you're on **Windows**, the application will start, and the user interface defined in `modiule/UI.py` will be displayed.

## Notes

- This project is designed for **Windows** (`sys.platform == "win32"`).
- Make sure Python is installed and properly configured on your machine.

---

This version includes clear sections, headers, and improved readability while keeping the information structured and concise. Let me know if you need any more adjustments!
