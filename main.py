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
    
    hash_map: dict["hashlib._Hash", list[str]]  = {}
    all_files: list[str] = []

    # Create a list of all files
    print(f"Counting number of files...")
    for root, _, files in os.walk(directory):
        for filename in files:
            full_path = os.path.join(root, filename)
            if os.path.basename(full_path) == "hash.json":
                continue

            all_files.append(full_path)

    # Process each file
    print(f"Hashing {len(all_files)} files in: {directory}")
    for full_path in tqdm(all_files, unit="file"):
        file_hash = compute_hash(full_path)
        if file_hash:
            # Check for duplicates
            if file_hash  not in hash_map:
                hash_map[file_hash] = []
            
            hash_map[file_hash].append(full_path)

        else:
            print(f"Failed to hash file: {full_path}")


    # Save hash map to a file
    hash_map_path = os.path.join(directory, "hash.json")
    with open(hash_map_path, 'w') as f:
        json.dump(hash_map, f, indent=2)
    
    return hash_map

def find_unbacked_files(backup_dir, source_dir):
    # --- Backup hash decision ---
    backup_hashes = None
    print("Looking for existing backup hash file.")
    backup_hash_path = os.path.join(backup_dir, "hash.json")
    if os.path.exists(backup_hash_path):
        response = input(
            f"Do you want to update hash map: '{backup_hash_path}'? (y/n): "
        ).strip().lower()
        if response != "y":
            print("Loading hash map for backup")
            with open(backup_hash_path, "r") as f:
                backup_hashes = json.load(f)
    else:
        print("No backup hash map found.")

    # --- Source hash decision ---
    source_hashes = None
    print("Looking for existing source hash file.")
    source_hash_path = os.path.join(source_dir, "hash.json")
    if os.path.exists(source_hash_path):
        response = input(
            f"Do you want to update hash map: '{source_hash_path}'? (y/n): "
        ).strip().lower()
        if response != "y":
            print("Loading hash map for source")
            with open(source_hash_path, "r") as f:
                source_hashes = json.load(f)
    else:
        print("No source hash map found.")

    # --- Slow operations (only if needed) ---
    if backup_hashes is None:
        print("Hashing backup directory...")
        backup_hashes = hash_files_in_directory(backup_dir)

    if source_hashes is None:
        print("Hashing source directory...")
        source_hashes = hash_files_in_directory(source_dir)

    # --- Generate output ---
    missing = []
    backed_up = []

    print("Generating output files...")
    for file_hash, file_paths in source_hashes.items():
        for fp in file_paths:
            if file_hash not in backup_hashes:
                missing.append(fp)
            else:
                backed_up.append(fp)

    return missing, backed_up

def delete_file(file):
    """Function to delete file after confirmation"""
    try:
        os.remove(file)
        print(f"Deleted: {file}")
    except Exception as e:
        print(f"Error deleting {file}: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find files in source that are not backed up (by content).")
    parser.add_argument(
        "backup",
        help="Path to the backup folder"
    )
    parser.add_argument(
        "source",
        help="Path to the source folder"
    )
    parser.add_argument(
        "-m", "--missing",
        help="Optional output file to save the list of files present in source, missing from backup."
    )
    parser.add_argument(
        "-b", "--backed",
        help="Optional output file to save the list of files present in source, already backed up."
    )
    parser.add_argument(
        "--delete_backed",
        action="store_true",
        help="Delete files that are already backed up. Asks for confirmation."
        )

    args = parser.parse_args()

    missing_files, duplicate_files = find_unbacked_files(args.backup, args.source)

    print(f"\nFound {len(missing_files)} files in source that are not in backup.")
    if missing_files:
        for path in missing_files:
            print(path)

        if args.missing:
            missing_file_path = os.path.join(args.source, args.missing)
            with open(missing_file_path, "w", encoding="utf-8") as out:
                for path in missing_files:
                    out.write(path + "\n")
            print(f"\nMissing file list saved to: {args.missing}")
    
    print(f"\nFound {len(duplicate_files)} files in source that ARE in backup.")
    if duplicate_files:
        for path in duplicate_files:
            print(path)

        if args.backed:
            backed_file_path = os.path.join(args.source, args.backed)
            with open(backed_file_path, "w", encoding="utf-8") as out:
                for path in duplicate_files:
                    out.write(path + "\n")
            print(f"\nRedundant file list saved to: {args.backed}")
    
    # If the user has confirmed the deletion, proceed with file removal
    if args.delete_backed:
        print("\nYou have chosen to delete source files that are already backed up. Please be very cautious!")
        confirm = input("Type 'confirm' to proceed with deletion: ").strip().lower()
        
        if confirm == 'confirm':
            if duplicate_files:
                for file in duplicate_files:
                    delete_file(file)
            else:
                print("No files found to delete.")
        else:
            print("Deletion action cancelled.")