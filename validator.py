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
    The Manifest file will be in JSON with the following structure:
        {
            "Summary": {
                "JSON": int,
                "Media": int,
                "Unique": int,
                "Duplicates": int,
                "Corrupted": int,
                "Missing": int
            },
            "Manifest": [
                {
                    "File_Name": str,
                    "File_Size": int,
                    "Timestamp": str,
                    "Validation_Status": str,  # Valid, Corrupted, Missing
                    "Instances": [
                        {
                            "Path": str,
                            "Download_URL": str
                        },
                        ...
                    ]
                },
                ...
            ],
            "Media_Errors": {
                "Missing Files": [str, ...],
                "Corrupted Files": [str, ...]
            }
        }
    '''

    manifest = {
        "Summary": {
            "JSON": 0,
            "Media": 0,
            "Unique": 0,
            "Duplicates": 0,
            "Corrupted": 0,
            "Missing": 0
        },
        "Manifest": [],
        "Media_Errors": {
            "Missing Files": [],
            "Corrupted Files": []
        }
    }

    media_items = set()
    duplicate_tracker = {}

    # Walk through the provided media root directory and validate files
    for root, dirs, files in os.walk(media_root, topdown=True):
        for file in files:
            json_file: dict = None

            # Only process JSON files for validation, media files will be 
            # validated based on the JSON metadata
            if file.endswith('supplemental-metada.json'):
                json_file: dict = json.load(open(join(root, file)))
                manifest["Summary"]["JSON"] += 1
            else:
                continue

            json_file_path: str = join(root, file)

            try:
                media_file_name: str = json_file.get("title")
                download_url: str = json_file.get("url")
                photo_taken_time: dict = json_file.get("photoTakenTime", {})
                timestamp: str = photo_taken_time.get("timestamp", "")

            except KeyError as e:
                print(f"Error parsing JSON file {json_file_path}: {e}")
                continue

            # Initialize validation fields
            file_size: int = 0
            validation_status: str = "Valid"

            # Check for media file existence and validate size
            try:
                media_file_path: str = join(root, media_file_name)
                file_size: int = getsize(media_file_path)

                # Files with size 0 are considered corrupted
                if file_size == 0:
                    validation_status = "Corrupted"
                    manifest["Summary"]["Corrupted"] += 1
                    manifest["Media_Errors"]["Corrupted Files"].append(
                        media_file_path)
                else:
                    # Successfully validated media file
                    manifest["Summary"]["Media"] += 1

            except OSError as e:
                msg: str = (f"Media missing for {media_file_path}: {e}")

                # If the media file is missing, mark it as such and add to the
                # manifest, but continue processing other files
                validation_status: str = "Missing"
                manifest["Summary"]["Missing"] += 1
                manifest["Media_Errors"]["Missing Files"].append(msg)
                continue

            # Track duplicates based on file name and size
            duplicate_key: tuple = (media_file_name, file_size)
            if duplicate_key in duplicate_tracker:
                duplicate_tracker[duplicate_key].append(
                    (media_file_path, download_url))
            else:
                duplicate_tracker[duplicate_key] = [(media_file_path, download_url)]

            # Build the record for the manifest
            record: tuple = (
                media_file_name,
                file_size,
                timestamp,
                validation_status
            )

            media_items.add(record)

    for item in media_items:
        file_name, file_size, timestamp, validation_status = item
        paths_and_downloads: list = duplicate_tracker.get((file_name, file_size), [])

        instances = []
        for path, download in paths_and_downloads:
            instances.append({
                "Path": path,
                "Download_URL": download
            })

        # Count duplicates beyond the first occurrence
        manifest["Summary"]["Duplicates"] += len(paths_and_downloads) - 1
        manifest["Summary"]["Unique"] += 1

        manifest["Manifest"].append({
            "File_Name": file_name,
            "File_Size": file_size,
            "Timestamp": timestamp,
            "Validation_Status": validation_status,
            "Instances": instances,
        })

    # Generate a timestamped manifest file name and save the manifest as JSON
    manifestFileName = f'manifest_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'

    with open(manifestFileName, 'w') as f:
        json.dump(manifest, f, indent=4)

    return manifestFileName


def pp_manifest(manifest_name: str) -> None:
    '''Pretty print the Manifest file'''

    with open(manifest_name, 'r') as f:
        manifest = json.load(f)

    for category, result in manifest["Summary"].items():
        print(f"{category}: {result}")

    if manifest["Media_Errors"]["Missing Files"]:
        print("\nMissing Files:")
        for missing in manifest["Media_Errors"]["Missing Files"]:
            print(f"  - {missing}")

    if manifest["Media_Errors"]["Corrupted Files"]:
        print("\nCorrupted Files:")
        for corrupted in manifest["Media_Errors"]["Corrupted Files"]:
            print(f"  - {corrupted}")


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
