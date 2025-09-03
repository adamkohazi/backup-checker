import os
import hashlib
import json
from tqdm import tqdm

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

def hash_files_in_directory(directory):
    """Recursively hash all files in a directory with a progress bar."""
    hash_map = {}
    all_files = []
    print(f"Counting number of files...")
    for root, _, files in os.walk(directory):
        for filename in files:
            full_path = os.path.join(root, filename)
            if os.path.basename(full_path) != "hash.json":
                all_files.append(full_path)

    print(f"Hashing {len(all_files)} files in: {directory}")
    for full_path in tqdm(all_files, unit="file"):
        file_hash = compute_hash(full_path)
        if file_hash:
            hash_map[file_hash] = full_path

    return hash_map

def load_or_create_hash_map(directory):
    """Load hash map from file or create a new one."""
    hash_map_path = os.path.join(directory, "hash.json")
    hash_map = {}

    if os.path.exists(hash_map_path):
        print(f"Found hash map in: {directory}")
        response = input(f"Do you want to update the hash map in '{directory}'? (y/n): ").strip().lower()
        if response == 'y':
            hash_map = hash_files_in_directory(directory)
            with open(hash_map_path, 'w') as f:
                json.dump(hash_map, f, indent=2)
        else:
            with open(hash_map_path, 'r') as f:
                hash_map = json.load(f)
    else:
        print(f"No hash map found in: {directory}. Creating one...")
        hash_map = hash_files_in_directory(directory)
        with open(hash_map_path, 'x') as f:
            json.dump(hash_map, f, indent=2)

    return hash_map

def find_unbacked_files(backup_dir, source_dir):
    """Find files in source not backed up in backup."""
    print(f"Scanning backup folder: {backup_dir}")
    backup_hashes = load_or_create_hash_map(backup_dir)
    print(f"Scanning source folder: {source_dir}")
    source_hashes = load_or_create_hash_map(source_dir)

    missing = []
    for file_hash, file_path in source_hashes.items():
        if file_hash not in backup_hashes:
            missing.append(file_path)

    return missing

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find files in source that are not backed up (by content).")
    parser.add_argument("backup", help="Path to the backup folder")
    parser.add_argument("source", help="Path to the source folder")
    parser.add_argument("-o", "--output", help="Optional output file to save the list")

    args = parser.parse_args()
    missing_files = find_unbacked_files(args.backup, args.source)

    print(f"\nFound {len(missing_files)} files in source that are not in backup.")
    if missing_files:
        for path in missing_files:
            print(path)

        if args.output:
            with open(args.output, "w") as out:
                for path in missing_files:
                    out.write(path + "\n")
            print(f"\nMissing file list saved to: {args.output}")