import os
import shutil
import subprocess

def find_folders_missing_trailer_file(root_folder):
    """
    Scans the immediate child folders of a root folder and identifies child folders that do not contain
    a file with the word 'trailer' in its name.

    Args:
        root_folder (str): The root folder to scan.

    Returns:
        list: A list of child folder paths that do not contain a 'trailer' file.
    """
    folders_without_trailer = []

    # Check only immediate child folders of the root folder
    for folder in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder)
        if os.path.isdir(folder_path):
            contains_trailer = any('trailer' in file.lower() for file in os.listdir(folder_path))

            # If no 'trailer' file is found, add to the list
            if not contains_trailer:
                folders_without_trailer.append(folder_path)

    return folders_without_trailer

def extract_video_id(nfo_content):
    """
    Extracts the YouTube video ID from the .nfo file content.

    Args:
        nfo_content (str): The content of the .nfo file.

    Returns:
        str: The extracted video ID, or None if not found.
    """
    
    start_tag = "?video_id="
    end_tag = "</trailer>"
    start_index = nfo_content.find(start_tag)

    if start_index == -1:
        print("DEBUG: start_tag not found in nfo_content")
        return None

    start_index += len(start_tag)
    end_index = nfo_content.find(end_tag, start_index)

    print(f"DEBUG: start_index={start_index}, end_index={end_index}")

    if end_index == -1 or start_index >= end_index:
        print("DEBUG: Invalid video ID positions")
        return None

    video_id = nfo_content[start_index:end_index].strip()
    print(f"DEBUG: video_id={video_id}")
    return video_id

def download_trailer_videos(folders, working_directory):
    """
    For each folder, find the .nfo file in the child folder, extract the YouTube URL, and download the video.

    Args:
        folders (list): List of folder paths missing a 'trailer' file.
        working_directory (str): Directory to save the downloaded videos.

    Returns:
        tuple: Number of successful downloads and number of failures.
    """
    successful_downloads = 0
    failed_downloads = 0

    for folder in folders:
        nfo_files = [f for f in os.listdir(folder) if f.endswith('.nfo')]

        print(f"DEBUG: nfo_files={nfo_files}")

        if not nfo_files:
            print(f"No .nfo file found in folder: {folder}")
            failed_downloads += 1
            continue

        nfo_file_path = os.path.join(folder, nfo_files[0])

        try:
            # Read the .nfo file and extract the YouTube video ID
            try:
                with open(nfo_file_path, 'r', encoding='ansi') as nfo_file:
                    nfo_content = nfo_file.read()
            except UnicodeDecodeError:
                print(f"DEBUG: UnicodeDecodeError for {nfo_file_path}. Retrying with 'utf-8' encoding.")
                with open(nfo_file_path, 'r', encoding='utf-8', errors='ignore') as nfo_file:
                    nfo_content = nfo_file.read()

            print(f"DEBUG: nfo_content={nfo_content[:100]}...")

            video_id = extract_video_id(nfo_content)
            if not video_id:
                print(f"No valid trailer tag or video ID found in .nfo file: {nfo_file_path}")
                failed_downloads += 1
                continue

            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"DEBUG: youtube_url={youtube_url}")

            # Construct output file name
            output_file_name = os.path.basename(folder) + "-trailer.mp4"
            temp_output_path = os.path.join(working_directory, output_file_name)

            # Download the YouTube video with the specified format using ytdl
            print(f"Downloading {youtube_url} to {temp_output_path}")
            subprocess.run([
                "yt-dlp", "-o", temp_output_path, "--format", "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best", "--merge-output-format", "mp4", youtube_url
            ], check=True)

            # Move the downloaded file to the corresponding folder
            final_output_path = os.path.join(folder, output_file_name)
            print(f"Moving file to {final_output_path}")
            shutil.move(temp_output_path, final_output_path)

            successful_downloads += 1

        except (IndexError, FileNotFoundError) as e:
            print(f"Error reading .nfo file in folder: {folder}. Exception: {e}")
            failed_downloads += 1
        except subprocess.CalledProcessError as e:
            print(f"Error downloading video: {e}")
            failed_downloads += 1

    return successful_downloads, failed_downloads

def main():
    # Specify the root folder to scan
    root_folder = input("Enter the path to the root folder to scan: ").strip()

    if not os.path.exists(root_folder):
        print(f"Error: The path {root_folder} does not exist.")
        return

    # Specify the working directory for saving temporary videos
    working_directory = os.getcwd()

    # Find child folders missing 'trailer' files
    missing_trailer_folders = find_folders_missing_trailer_file(root_folder)

    # Output the results
    if missing_trailer_folders:
        print("The following child folders do not contain a file with 'trailer' in its name:")
        for folder in missing_trailer_folders:
            print(folder)

        # Download trailers for missing folders
        successful, failed = download_trailer_videos(missing_trailer_folders, working_directory)

        # Provide a summary
        print("\nSummary:")
        print(f"Total child folders without trailer files: {len(missing_trailer_folders)}")
        print(f"Successfully downloaded trailers: {successful}")
        print(f"Child folders still missing trailers: {failed}")
    else:
        print("All child folders contain a file with 'trailer' in its name.")

if __name__ == "__main__":
    main()
