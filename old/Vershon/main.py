import os
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import mimetypes

# Function to download a chunk of the file
async def download_chunk(client, url, start_byte, end_byte, download_path, filename):
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        part_filename = os.path.join(download_path, f"{filename}_part{start_byte}-{end_byte}")
        
        with open(part_filename, 'ab') as file:  # Use 'ab' to append to the existing file
            file.write(response.content)
        
        # Confirm that the part file was successfully written
        if os.path.exists(part_filename):
            print(f"Downloaded part {part_filename}")
        else:
            print(f"Failed to download part {part_filename}")
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error downloading chunk: {e}")

# Function to download the file in multiple connections
async def multi_connection_download(url, download_path, filename, num_connections=4, pkg_size=1024 * 1024, use_threads=False, num_threads=4):
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

        # Choose between threads or async download function
        download_func = download_chunk if not use_threads else download_chunk

        # Download in multiple chunks
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i in range(num_connections):
                task = asyncio.ensure_future(
                    download_func(client, url, start_bytes[i], end_bytes[i], download_path, filename))
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
    # Extract the base filename from the URL path
    base_filename = os.path.basename(urlsplit(url).path)
    
    # If the filename is missing, extract from the Content-Disposition header or use default
    if not base_filename:
        base_filename = url.split('/')[-1] or "downloaded_file"
    
    # Try to determine the file extension using the MIME type
    mime_type, _ = mimetypes.guess_type(base_filename)
    if not mime_type:
        return base_filename  # Return as-is if MIME type is unknown

    extension = mime_type.split('/')[1]
    if '.' not in base_filename:
        base_filename += f".{extension}"

    return base_filename

# Main download trigger function
def trigger_download():
    download_url = "https://vscode.download.prss.microsoft.com/dbazure/download/stable/91fbdddc47bc9c09064bf7acf133d22631cbf083/VSCodeUserSetup-x64-1.96.3.exe"  # Update with your URL
    
    # Auto-detect the filename
    filename = extract_filename_from_url(download_url)

    download_path = "downloads"  # Parent folder to store the downloaded parts

    # Ensure the parent download folder exists
    os.makedirs(download_path, exist_ok=True)

    # Adjust parameters if needed
    num_connections = 20  # Number of concurrent connections for the download
    package_size = 1024 * 1024  # 1MB chunk size
    use_threads = False  # Use asyncio or threads for downloading
    num_threads = 4  # Number of threads to use if 'use_threads' is True

    # Start the download process
    asyncio.run(multi_connection_download(download_url, download_path, filename, num_connections, package_size, use_threads, num_threads))

    # Remove unwanted temporary parts after the download is completed
    for part_file in os.listdir(download_path):
        if part_file.startswith(f"{filename}_part"):
            os.remove(os.path.join(download_path, part_file))

    print(f"Download completed and cleaned up: {filename}")

if __name__ == "__main__":
    trigger_download()
