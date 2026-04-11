#!/usr/bin/env python3

'''Validator via Manifest Generation for Google Images Takeout data'''

import os
from os.path import join, getsize
import json


def generate_manifest():
    '''
    Generate a Manifest file with the validation results. \n
    The Manifest file should be in JSON format and contain the following:
    - Report
        - Total number of JSON files
        - Total number of media files
        - Missing Files
        - Duplicate Files
        - Corrupted Files
    - Manifest
        - File Name
        - File Size
        - Timestamp
        - Download URL
        - Validation Status (Valid, Missing, Duplicate, Corrupted)
        - Validation Errors (if any)
    '''

    manifest = {
        "Report": {
            "Total JSON Files": 0,
            "Total Media Files": 0,
            "Missing Files": [],
            "Duplicate Files": [],
            "Corrupted Files": []
        },
        "Manifest": []
    }

    # A dictionary to track file names and jsonfiles and their occurrences for
    #   duplicate detection
    # TODO: duplicate_tracking = {}

    # Walk through the current directory and validate files
    for root, dirs, files in os.walk(
            './GoogleTakeoutTest/Consolidated/',
            topdown=True):
        for file in files:
            json_file = None

            if file.endswith('supplemental-metada.json'):
                json_file = json.load(open(join(root, file)))
                manifest["Report"]["Total JSON Files"] += 1
            elif file.endswith(('.jpg', '.png', '.mp4', '.avi')):
                # Check for duplicates based on file name and size
                continue
            else:
                # Unsupported file type, skip validation
                continue

            file_path = join(root, file)
            try:
                file_name = json_file.get("title")
                download_url = json_file.get("url")
            except KeyError as e:
                print(f"Error parsing JSON file {file_path}: {e}")
                continue

            # Initialize validation fields
            timestamp = ""
            file_size = 0

            validation_status = "Valid"
            validation_errors = []

            photoTakenTime = json_file.get("PhotoTakenTime", None)
            if photoTakenTime:
                timestamp = photoTakenTime.get("timestamp", "")

            try:
                file_size = getsize(join(root, file_name))

                if file_size == 0:
                    validation_status = "Corrupted"
                    manifest["Report"]["Corrupted Files"].append(file_path)
                else:
                    manifest["Report"]["Total Media Files"] += 1

            except OSError as e:
                print(f"Error finding file {file_path}: {e}")

                validation_status = "Missing"
                validation_errors.append(str(e))

                manifest["Report"]["Missing Files"].append(file_path)

            manifest["Manifest"].append({
                "File Name": file_name,
                "File Size": file_size,
                "Timestamp": timestamp,
                "Download URL": download_url,
                "Validation Status": validation_status,
                "Validation Errors": validation_errors
            })

    manifest["Report"]["Total JSON Files"] = len(manifest["Manifest"])

    manifestFileName = 'manifest.json'

    # Save the manifest to a JSON file
    with open(manifestFileName, 'w') as f:
        json.dump(manifest, f, indent=4)

    return manifestFileName


def ppManifest(manifest_name):
    '''Pretty print the Manifest file'''

    with open(manifest_name, 'r') as f:
        manifest = json.load(f)

    print("Report:")
    print(f"Total JSON Files: {manifest['Report']['Total JSON Files']}")
    print(f"Total Media Files: {manifest['Report']['Total Media Files']}")
    print(f"Missing Files: {len(manifest['Report']['Missing Files'])}")
    print(f"Duplicate Files: {len(manifest['Report']['Duplicate Files'])}")
    print(f"Corrupted Files: {len(manifest['Report']['Corrupted Files'])}")


def main():
    '''
    Validate the data in current head of directory. Generate a Manifest file
    with the validation results. Print the validation report to the console.
    '''

    manifest_name = generate_manifest()

    ppManifest(manifest_name)


if __name__ == "__main__":
    print("This is the validator module.")
    main()
