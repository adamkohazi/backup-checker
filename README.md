# 🗄️ Backup checker
This script looks at files in a source folder and checks if they are already present in a backup folder.

## 🚧 Current State
Please note this is a crude, untested script at the moment, use it at your own risk.
I may or may not return to it in the future to imrpove or polish it.

## ⚙️ How it works
- The script computes the SHA-256 hash of all files in the source and backup directories.
- Stores the hashes in .json files in the respective folders, so they don't need to be recalculated every time.
- Identifies files in the source directory that are not backed up by comparing file hashes.
- Displays the list of missing files. (Optionally saves the list to a file.)

## ❓ How to use
To run the script, you need to specify both the backup and source directories. 
```bash
python script_name.py <backup_directory> <source_directory>
```
If a hash.json file already exists in the specified folders, the script will ask if you want to update them or not. 

Optionally you can export the list of missing files (that are present in source, but not in backup).
```bash
python script_name.py <backup_directory> <source_directory> -m <filname>
```

You can also export the list of files that are already backed up (that are present in source and also in backup)
```bash
python script_name.py <backup_directory> <source_directory> -b <filname>
```

Example usage:
```bash
python main.py C:\backup\ d:\source\ -m missing.txt -b backed.txt
```

## 🐛 Known bugs
- Unicode characters in filenames may cause issues.
- Potential duplicate files to be added to missing or backed.
- Empty directories to be deleted during deletion.
