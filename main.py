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

def hash_files_in_directory(directory, duplicate_strategy = 'warn'):
    """Recursively hash all files in a directory with a progress bar."""
    
    hash_map: dict["hashlib._Hash", str]  = {}
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
            if file_hash in hash_map:
                match duplicate_strategy:
                    case 'warn':
                        print(f"Potential duplicate file: {full_path}")
                    case 'ask':
                        print(f"  1 - {hash_map[file_hash]}")
                        print(f"   2 - {full_path}")
                        print("   a - Keep both versions")
                        while True:
                            choice = input("Which file do you want to keep? (1/2/a) " )
                            match choice:
                                case '1':
                                    delete_file(full_path)
                                    break
                                case '2':
                                    delete_file(hash_map[file_hash])
                                    hash_map[file_hash] = full_path
                                    break
                                case 'a':
                                    print("Both files kept.")
                                    break
                                case _:
                                    print("Wrong input, please try again.")

                    case 'delete':
                        # Make sure the files are duplicates
                        filename1, extension1 = os.path.splitext(os.path.basename(hash_map[file_hash]))
                        filename2, extension2 = os.path.splitext(os.path.basename(full_path))

                        if (extension1 == extension2) and ((filename1 in filename2) or (filename2 in filename1)):
                            # If already hashed file is older
                            if(os.stat(full_path).st_ctime >= os.stat(hash_map[file_hash]).st_ctime):
                                delete_file(full_path)
                            # If new one is older
                            else:
                                delete_file(hash_map[file_hash])
                                hash_map[file_hash] = full_path
                        else:
                            print(f"Ambigous files, keeping both.")
                            print(f"   1 - {hash_map[file_hash]}")
                            print(f"   2 - {full_path}")

            else:
                hash_map[file_hash] = full_path

    # Save hash map to a file
    hash_map_path = os.path.join(directory, "hash.json")
    with open(hash_map_path, 'w') as f:
        json.dump(hash_map, f, indent=2)
    
    return hash_map

def load_or_create_hash_map(directory, duplicate_strategy):
    """Load hash map from file or create a new one."""
    hash_map_path = os.path.join(directory, "hash.json")
    hash_map = {}

    if os.path.exists(hash_map_path):
        print(f"Found hash map in: {directory}")
        response = input(f"Do you want to update the hash map in '{directory}'? (y/n): ").strip().lower()
        if response == 'y':
            hash_map = hash_files_in_directory(directory, duplicate_strategy)
        else:
            with open(hash_map_path, 'r') as f:
                hash_map = json.load(f)
    else:
        print(f"No hash map found in: {directory}. Creating one...")
        hash_map = hash_files_in_directory(directory, duplicate_strategy)

    return hash_map

def find_unbacked_files(backup_dir, source_dir, duplicate_strategy):
    """Find files in source not backed up in backup."""
    print(f"Scanning backup folder: {backup_dir}")
    backup_hashes = load_or_create_hash_map(backup_dir, 'warn')
    print(f"Scanning source folder: {source_dir}")
    source_hashes = load_or_create_hash_map(source_dir, duplicate_strategy)

    missing = []
    backed_up = []

    for file_hash, file_path in source_hashes.items():
        if file_hash not in backup_hashes:
            missing.append(file_path)
        else:
            backed_up.append(file_path)

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

    parser.add_argument(
        "--duplicate_strategy", 
        choices=["warn", "ask", "delete"], 
        default="warn", 
        help="How to handle duplicate source files: 'warn', 'ask', or 'delete'. Default is 'warn'."
    )
    args = parser.parse_args()

    if args.duplicate_strategy == 'delete':
        print("\nYou have chosen to delete duplicate source files. Please be very cautious!")
        confirm = input("Type 'confirm' to proceed with deletion: ").strip().lower()
        
        if confirm != 'confirm':
            args.duplicate_strategy = 'warn'
            input("Deletion action cancelled. Setting duplicate mode to 'warn' instead. Press any key to continue...")


    missing_files, duplicate_files = find_unbacked_files(args.backup, args.source, args.duplicate_strategy)

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