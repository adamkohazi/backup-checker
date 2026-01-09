import os
import hashlib
import json
from tqdm import tqdm

def compute_hash(file_path, chunk_size=1024 * 1024):
    """Compute SHA-256 hash of a file."""
    try:
        with open(file_path, "rb") as f:
            return hashlib.file_digest(f, "sha256").hexdigest()
    except Exception as e:
        print(f"Error hashing {file_path}: {e}")
        return None

def hash_files(directory):
    """Recursively hash all files in a directory with a progress bar."""
    
    hash_map: dict[str, list[str]]  = {}
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
    for full_path in tqdm(all_files, mininterval=0.5, smoothing=0.0, unit="file"):
        file_hash = compute_hash(full_path)

        if file_hash:
            # Check for duplicates
            if file_hash  not in hash_map:
                hash_map[file_hash] = []
            
            hash_map[file_hash].append(full_path)

        else:
            tqdm.write(f"Failed to hash file: {full_path}")


    # Save hash map to a file
    hash_map_path = os.path.join(directory, "hash.json")
    with open(hash_map_path, 'w') as f:
        json.dump(hash_map, f, indent=2)
    
    return hash_map

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
        "source",
        help="Path to the source folder"
    )
    parser.add_argument(
        "backup",
        help="Path to the backup folder"
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
        "-sd", "--source_duplicates",
        help="Optional output file to save the list of duplicate files in the source folder."
    )
    parser.add_argument(
        "-bd", "--backup_duplicates",
        help="Optional output file to save the list of duplicate files in the source folder."
    )
    parser.add_argument(
        "--delete_duplicates",
        action="store_true",
        help="Delete duplicate files from source. Asks for confirmation."
    )
    parser.add_argument(
        "--delete_backed",
        action="store_true",
        help="Delete files that are already backed up. Asks for confirmation."
    )

    args = parser.parse_args()

    # --- Backup hash decision ---
    backup_hashes = None
    print("Looking for existing backup hash file...")
    backup_hash_path = os.path.join(args.backup, "hash.json")
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
    print("\nLooking for existing source hash file...")
    source_hash_path = os.path.join(args.source, "hash.json")
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
        print("\nHashing backup directory...")
        backup_hashes = hash_files(args.backup)

    if source_hashes is None:
        print("\nHashing source directory...")
        source_hashes = hash_files(args.source)

    # --- Collect missing / duplicate files ---
    missing_files: list[list[str]] = []
    backed_up_files: list[str] = []

    print("\nGenerating output files...")
    for file_hash, file_paths in source_hashes.items():
        if file_hash in backup_hashes:
            for fp in file_paths:
                backed_up_files.append(fp)
                
        else:
            missing_files.append(file_paths)
                
    
    if missing_files:
        print(f"\n{len(missing_files)} unique files found in source that are not in backup.")

        if args.missing:
            missing_file_path = os.path.join(args.source, args.missing)
            with open(missing_file_path, "w", encoding="utf-8") as out:
                for unique in missing_files:
                    out.write(f"{unique[0]}\n")
                    for fp in unique[1:]:
                        out.write(f"\t{fp}\n")
            print(f"Missing file list saved to: {missing_file_path}")
    else:
        print(f"\nGood news! Every file in source has already been backed up.")

    
    if backed_up_files:
        print(f"\n{len(backed_up_files)} files found in source that ARE in backup.")

        if args.backed:
            backed_file_path = os.path.join(args.source, args.backed)
            with open(backed_file_path, "w", encoding="utf-8") as out:
                for path in backed_up_files:
                    out.write(path + "\n")
            print(f"Redundant file list saved to: {backed_file_path}")
    else:
        print(f"\nNone of the files in source are backed up!")


    print(f"\n{sum([len(paths)-1 for paths in source_hashes.values() if len(paths)>1])} duplicate files found in the source folder.")
    if args.source_duplicates:
        source_duplicate_file_path = os.path.join(args.source, args.source_duplicates)
        with open(source_duplicate_file_path, "w", encoding="utf-8") as out:
            for file_paths in source_hashes.values():
                if len(file_paths) > 1:
                    out.write(f"File: {os.path.basename(file_paths[0])}\n")
                    for fp in file_paths:
                        out.write(f"\t{fp}\n")
        print(f"Duplicate files in source saved to: {source_duplicate_file_path}")
    
    print(f"\n{sum([len(paths)-1 for paths in backup_hashes.values() if len(paths)>1])} duplicate files found in the backup folder.")
    if args.backup_duplicates:
        backup_duplicate_file_path = os.path.join(args.backup, args.backup_duplicates)
        with open(backup_duplicate_file_path, "w", encoding="utf-8") as out:
            for file_paths in backup_hashes.values():
                if len(file_paths) > 1:
                    out.write(f"File: {os.path.basename(file_paths[0])}\n")
                    for fp in file_paths:
                        out.write(f"\t{fp}\n")
        print(f"Duplicate files in backup saved to: {backup_duplicate_file_path}")
    
    ##
    if args.delete_duplicates:
        # If the user has confirmed the deletion, proceed with file removal
        print("\nYou have chosen to delete duplicate source files. Please be very cautious!")
        confirm = input("Type 'confirm' to proceed with deletion: ").strip().lower()
        
        if confirm == 'confirm':
            for file_paths in source_hashes.values():
                for fp in file_paths[1:]:
                    delete_file(fp)
        
                    # Delete directory if it has become empty
                    dir_path = os.path.dirname(fp)
                    while dir_path and os.path.isdir(dir_path):
                        try:
                            os.rmdir(dir_path)  # only works if empty
                        except OSError:
                            break  # directory not empty
                        dir_path = os.path.dirname(dir_path)
        else:
            print("Deletion action cancelled.")
        

    if args.delete_backed:
        if backed_up_files:
            # If the user has confirmed the deletion, proceed with file removal
            print("\nYou have chosen to delete source files that are already backed up. Please be very cautious!")
            confirm = input("Type 'confirm' to proceed with deletion: ").strip().lower()
            
            if confirm == 'confirm':
                for file in backed_up_files:
                    delete_file(file)
                
                # Delete directory if it has become empty
                dir_path = os.path.dirname(file)
                while dir_path and os.path.isdir(dir_path):
                    try:
                        os.rmdir(dir_path)  # only works if empty
                    except OSError:
                        break  # directory not empty
                    dir_path = os.path.dirname(dir_path)
            else:
                print("Deletion action cancelled.")
        else:
            print("\nNothing to delete, everything needs to be backed up!")

