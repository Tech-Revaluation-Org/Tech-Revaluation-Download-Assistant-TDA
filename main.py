import os
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor


async def download_chunk(client, url, start_byte, end_byte, download_path):
  headers = {'Range': f'bytes={start_byte}-{end_byte}'}
  response = await client.get(url, headers=headers)

  filename = os.path.join(download_path,
                          f"downloaded_file_part{start_byte}-{end_byte}")
  with open(filename,
            'ab') as file:  # Use 'ab' mode to append to existing file
    file.write(response.content)


async def multi_connection_download(url,
                                    download_path,
                                    num_connections=4,
                                    pkg_size=1024 * 1024,
                                    use_threads=False,
                                    num_threads=4):
  # Create the download path if it doesn't exist
  os.makedirs(download_path, exist_ok=True)

  async with httpx.AsyncClient() as client:
    response = await client.head(url)
    file_size = int(response.headers['Content-Length'])
    chunk_size = min(file_size // num_connections, pkg_size)

    tasks = []

    # Determine the starting byte for each chunk
    start_bytes = [i * chunk_size for i in range(num_connections)]
    end_bytes = [
        (i + 1) * chunk_size - 1 if i != num_connections - 1 else file_size - 1
        for i in range(num_connections)
    ]

    # Check if partially downloaded files exist and adjust start/end bytes accordingly
    for i in range(num_connections):
      part_filename = os.path.join(
          download_path,
          f"downloaded_file_part{start_bytes[i]}-{end_bytes[i]}")
      if os.path.exists(part_filename):
        with open(part_filename, 'rb') as part_file:
          if len(part_file.read()) == end_bytes[i] - start_bytes[i] + 1:
            continue  # File already downloaded completely
          else:
            start_bytes[i] = os.path.getsize(part_filename)

    # Choose between using threads or async for download_chunk function
    download_func = download_chunk if not use_threads else download_chunk

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
      for i in range(num_connections):
        task = asyncio.ensure_future(
            download_func(client, url, start_bytes[i], end_bytes[i],
                          download_path))
        tasks.append(task)

      # Wait for all downloads to complete
      await asyncio.gather(*tasks)

  # Combine the downloaded parts into a single file
  with open(os.path.join(download_path, "downloaded_file"),
            'wb') as output_file:
    for i in range(num_connections):
      part_filename = os.path.join(
          download_path,
          f"downloaded_file_part{start_bytes[i]}-{end_bytes[i]}")

      with open(part_filename, 'rb') as part_file:
        output_file.write(part_file.read())
      os.remove(part_filename)


def trigger_download():
  download_url = "" #downlode url
  download_path = r"Download"#carrent path make sure full path
  num_connections = 29  # Adjust the number of connections based on your system's capabilities
  package_size = 1024 * 1024  # 1 MB, adjust as needed
  use_threads = True  # Set to True to use threads, False to use asyncio
  num_threads = 4  # Adjust the number of threads based on your system's capabilities

  asyncio.run(
      multi_connection_download(download_url, download_path, num_connections,
                                package_size, use_threads, num_threads))


if __name__ == "__main__":
  trigger_download()
