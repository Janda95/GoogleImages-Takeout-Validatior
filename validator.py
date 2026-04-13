#!/usr/bin/env python3

'''Validator via Manifest Generation for Google Images Takeout data'''

import argparse
import os
from os.path import join, getsize
import json


def generate_manifest(media_root: str) -> str:
    '''
    Generate a Manifest file with the validation results. \n
    media_root: path to the root directory containing the media and JSON files
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

    # Build an index of all media files by (name, size) so duplicates can be detected
    media_index = {}
    for root, dirs, files in os.walk(media_root, topdown=True):
        for file in files:
            if file.endswith(('.jpg', '.png', '.mp4', '.avi')):
                file_path = join(root, file)
                try:
                    size = getsize(file_path)
                except OSError:
                    continue
                media_index.setdefault((file, size), []).append(file_path)

    duplicate_keys = {key for key, paths in media_index.items() if len(paths) > 1}
    manifest["Report"]["Duplicate Files"] = [path for paths in media_index.values() if len(paths) > 1 for path in paths]

    # Walk through the provided media root directory and validate files
    for root, dirs, files in os.walk(media_root, topdown=True):
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
                media_path = join(root, file_name)
                file_size = getsize(media_path)

                if file_size == 0:
                    validation_status = "Corrupted"
                    manifest["Report"]["Corrupted Files"].append(file_path)
                else:
                    manifest["Report"]["Total Media Files"] += 1
                    if (file_name, file_size) in duplicate_keys:
                        validation_status = "Duplicate"

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


def ppManifest(manifest_name: str) -> None:
    '''Pretty print the Manifest file'''

    with open(manifest_name, 'r') as f:
        manifest = json.load(f)

    print("Report:")
    print(f"Total JSON Files: {manifest['Report']['Total JSON Files']}")
    print(f"Total Media Files: {manifest['Report']['Total Media Files']}")
    print(f"Missing Files: {len(manifest['Report']['Missing Files'])}")
    print(f"Duplicate Files: {len(manifest['Report']['Duplicate Files'])}")
    print(f"Corrupted Files: {len(manifest['Report']['Corrupted Files'])}")


def main() -> None:
    '''
    Validate the data from a root media directory. Generate a Manifest file
    with the validation results. Print the validation report to the console.
    '''

    parser = argparse.ArgumentParser(
        description='Validate Google Takeout media JSON and generate a manifest.')
    parser.add_argument(
        '--media-root',
        default='./GoogleTakeoutTest/Consolidated/',
        help='Path to the root directory containing the media and JSON files.')
    args = parser.parse_args()

    manifest_name = generate_manifest(args.media_root)
    ppManifest(manifest_name)


if __name__ == "__main__":
    print("This is the validator module.")
    main()
