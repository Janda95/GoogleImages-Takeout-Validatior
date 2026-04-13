#!/usr/bin/env python3

'''Validator via Manifest Generation for Google Images Takeout data'''

import argparse
import os
from datetime import datetime
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
        - Total number of duplicate files
        - Total number of corrupted files
        - Total number of missing files
    - Manifest
        - File Name
        - File Size
        - Timestamp
        - Download URL
        - Validation Status (Valid, Missing, Duplicate, Corrupted)
        - Validation Errors (if any)
    - Duplicate Files (if any) - a list of duplicate file names and their paths
    - Errors
        - Missing Files (if any) - a list of missing file names and their paths
        - Corrupted Files (if any) - a list of corrupted file names and their paths
    '''

    manifest = {
        "Report": {
            "Total JSON Files": 0,
            "Total Media Files": 0,
            "Total Duplicate Files": 0,
            "Total Corrupted Files": 0,
            "Total Missing Files": 0
        },
        "Manifest": []
    }

    # Build an index of all media files by (name, size) so duplicates can be detected
    duplicate_files = build_media_index(media_root)

    if duplicate_files:
        manifest["Duplicate Files"] = duplicate_files
        manifest["Report"]["Total Duplicate Files"] = len(duplicate_files)

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
                    manifest["Report"]["Total Corrupted Files"] += 1
                    if "Errors" not in manifest:
                        manifest["Errors"] = {
                            "Missing Files": [],
                            "Corrupted Files": []
                        }
                    manifest["Errors"]["Corrupted Files"].append(file_path)
                else:
                    manifest["Report"]["Total Media Files"] += 1
                    if file_name in duplicate_files:
                        validation_status = "Duplicate"

            except OSError as e:
                print(f"Error finding file {file_path}: {e}")

                validation_status = "Missing"
                validation_errors.append(str(e))
                manifest["Report"]["Total Missing Files"] += 1
                if "Errors" not in manifest:
                    manifest["Errors"] = {
                        "Missing Files": [],
                        "Corrupted Files": []
                    }
                manifest["Errors"]["Missing Files"].append(file_path)

            manifest["Manifest"].append({
                "File Name": file_name,
                "File Size": file_size,
                "Timestamp": timestamp,
                "Download URL": download_url,
                "Validation Status": validation_status,
                "Validation Errors": validation_errors
            })

    manifest["Report"]["Total JSON Files"] = len(manifest["Manifest"])

    manifestFileName = f'manifest_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'

    # Save the manifest to a JSON file
    with open(manifestFileName, 'w') as f:
        json.dump(manifest, f, indent=4)

    return manifestFileName


def build_media_index(media_root: str) -> dict[str, list[str]]:
    '''Build an index of media files by (name, size) for duplicate detection'''

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

    duplicate_files = {}

    # Build a dictionary of duplicate file names to their paths
    for (file_name, _size), paths in media_index.items():
        if len(paths) > 1:
            duplicate_files.setdefault(file_name, []).extend(paths)

    return duplicate_files


def pp_manifest(manifest_name: str) -> None:
    '''Pretty print the Manifest file'''

    with open(manifest_name, 'r') as f:
        manifest = json.load(f)

    print("Report:")
    print(f"Total JSON Files: {manifest['Report']['Total JSON Files']}")
    print(f"Total Media Files: {manifest['Report']['Total Media Files']}")
    print(f"Total Duplicate Files: {manifest['Report']['Total Duplicate Files']}")
    print(f"Total Corrupted Files: {manifest['Report']['Total Corrupted Files']}")
    print(f"Total Missing Files: {manifest['Report']['Total Missing Files']}")

    if manifest.get("Errors"):
        print(f"Missing Files: {len(manifest['Errors']['Missing Files'])}")
        print(f"Corrupted Files: {len(manifest['Errors']['Corrupted Files'])}")

    if manifest.get("Duplicate Files"):
        print(f"Duplicate Names: {len(manifest['Duplicate Files'])}")


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
    pp_manifest(manifest_name)


if __name__ == "__main__":
    print("This is the validator module.")
    main()
