import os


def delete_file_from_server(file_path):
    try:
        # Remove the file from the file system
        os.remove(file_path)
    except OSError:
        # If the file does not exist or cannot be removed, raise an error
        raise ValueError(f"Error: {file_path} cannot be removed")
