import os
import argparse
from tqdm import tqdm
import hashlib
import re

def delete_file(file):
    """Function to delete file after confirmation"""
    try:
        os.remove(file)
        print(f"Deleted: {file}")
    except Exception as e:
        print(f"Error deleting {file}: {e}")

def compute_hash(file_path):
    """Compute SHA-256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Error hashing {file_path}: {e}")
        return None

def remove_duplicates(directory):
    all_files = []
    print(f"Counting number of files...")
    for root, _, files in os.walk(directory):
        for filename in files:
            full_path = os.path.join(root, filename)
            if os.path.basename(full_path) != "hash.json":
                all_files.append(full_path)

    print(f"Checking {len(all_files)} files in: {directory}")
    for full_path in tqdm(all_files, unit="file"):
        directory = os.path.dirname(full_path)
        filename, extension = os.path.splitext(os.path.basename(full_path))
        file_hash = compute_hash(full_path)
        
        # Check if filename ends in a number e.g. " (1)"
        if re.search(r" \(\d+\)$", filename):
            # Replace the pattern with an empty string
            stem = re.sub(r" \(\d+\)$", '', filename)

            # Check if there's a file with this name
            new_path = os.path.join(directory, stem+extension)
            if os.path.exists(new_path):

                # Check if they have the same content
                new_hash = compute_hash(new_path)
                if(file_hash == new_hash):
                    # print(f"Deleted: {full_path}")
                    # print(f"Kept  : {new_path}")
                    delete_file(full_path)

parser = argparse.ArgumentParser(description="Find files in source that are not backed up (by content).")
parser.add_argument("directory", help="Path to the folder")

args = parser.parse_args()

remove_duplicates(args.directory)