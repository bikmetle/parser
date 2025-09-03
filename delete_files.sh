#!/bin/bash

search_patterns=("google.com/" "yandex.com/" "mozilla.com/" "mozilla.net/" "google-analytics.com/" '"mimeType": "text/css"' '"mimeType": "font/woff"' '"mimeType": "image/svg+xml"')

delete_files_containing_patterns() {
    local pattern
    local exclude_file="delete_files.sh"

    for pattern in "${search_patterns[@]}"; do
        files_to_delete=$(find . -type f -name "*.json" -exec grep -l "$pattern" {} + | grep -v "$exclude_file")

        if [ -n "$files_to_delete" ]; then
            echo "$files_to_delete" | xargs rm -f
            echo "Files containing '$pattern' (excluding '$exclude_file') have been deleted."
        else
            echo "No files containing '$pattern' (excluding '$exclude_file') found."
        fi
    done
}

delete_files_containing_patterns


# Check if search text is provided as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <search_text>"
    exit 1
fi

search_text="$1"

# Use grep to find files containing the specified text
# -l: Only print the names of files containing the pattern
# -r: Recursively search subdirectories
files_to_delete=$(grep -lr "$search_text" .)

# Check if any files were found before proceeding with deletion
if [ -n "$files_to_delete" ]; then
    # Use xargs to pass the file names to rm for deletion
    echo "$files_to_delete" | xargs rm -f
    echo "Files containing '$search_text' have been deleted."
else
    echo "No files containing '$search_text' found."
fi
