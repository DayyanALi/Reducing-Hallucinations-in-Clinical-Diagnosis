import os

def rename_files(directory_path):
    # Verify the directory exists
    if not os.path.exists(directory_path):
        print(f"Error: The directory '{directory_path}' does not exist.")
        return

    # Counter for renamed files
    renamed_count = 0

    print(f"Scanning directory: {directory_path}\n")

    # List all files in the directory
    for filename in os.listdir(directory_path):
        # Create full file path
        old_file_path = os.path.join(directory_path, filename)

        # Skip if it's a directory, we only want files
        if not os.path.isfile(old_file_path):
            continue

        # Check if "_facts" is in the filename
        if "_facts" in filename:
            # Create the new filename by replacing "_facts" with an empty string
            # We use replace() so it works regardless of where "_facts" is (middle or end)
            new_filename = filename.replace("_facts", "")
            
            new_file_path = os.path.join(directory_path, new_filename)

            try:
                # Rename the file
                os.rename(old_file_path, new_file_path)
                print(f"[RENAMED] {filename} -> {new_filename}")
                renamed_count += 1
            except OSError as e:
                print(f"[ERROR] Could not rename {filename}: {e}")
        else:
            # Optional: Print files that were skipped
            print(f"[SKIPPED] {filename} (No '_facts' found)")
            pass

    print(f"\nProcessing complete. Total files renamed: {renamed_count}")

# path from your request
folder_path = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\data\babylon_data\babylon_notes_facts"

# Run the function
rename_files(folder_path)