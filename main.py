import sys
import os

# Check if the operating system is Windows
if sys.platform == "win32":
    # Ensure the 'modiule' directory is in the module search path
    sys.path.append(os.path.join(os.getcwd(), "modiule"))
    
    # Import and run the UI file
    try:
        import UI  # Assuming your main UI logic is in 'UI.py'
        print("UI module loaded successfully.")
    except ImportError as e:
        print(f"Error loading UI module: {e}")
        sys.exit(1)
else:
    print("This script is intended to run on a Windows system.")
    sys.exit(1)
