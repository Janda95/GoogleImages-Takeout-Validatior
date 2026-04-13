#!/usr/bin/env python3

'''Validator via Manifest Generation for Google Images Takeout data'''

import argparse
import os
from datetime import datetime
from os.path import getsize
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


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
                    "file_name": str,
                    "file_size": int,
                    "timestamp": str,
                    "validation_status": str,  # Valid, Corrupted, Missing
                    "instances": [
                        {
                            "path": str,
                            "download_url": str
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

    # Initialize the manifest structure with summary counts and error tracking
    manifest = {
        "Summary": {
            "JSON": 0,
            "Media": 0,
            "Unique": 0,
            "Duplicates": 0,
            "Corrupted": 0,
            "Missing": 0
        },
        "Manifest": []
    }

    media_items = []
    duplicate_tracker = defaultdict(list)

    # Walk through the provided media root directory and validate files
    for root, dirs, files in os.walk(Path(media_root), topdown=True):
        for file in files:
            json_file: Dict = None

            # Only process JSON files for validation, media files will be 
            # validated based on the JSON metadata
            if not file.endswith('supplemental-metada.json'):
                continue

            json_file_path: str = root + '/' + file

            with open(json_file_path, 'r') as f:
                try:
                    json_file = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON file {json_file_path}: {e}")
                    continue

            manifest["Summary"]["JSON"] += 1

            try:
                media_file_name: str = json_file.get("title")
                download_url: str = json_file.get("url")
                photo_taken_time: Dict = json_file.get("photoTakenTime", {})
                timestamp: str = photo_taken_time.get("timestamp", "")

            except KeyError as e:
                print(f"Error parsing JSON file {json_file_path}: {e}")
                continue

            # Initialize validation fields
            file_size: int = 0
            validation_status: str = "Valid"

            # Check for media file existence and validate size
            try:
                media_file_path: str = root + '/' + media_file_name
                file_size: int = getsize(media_file_path)

                # Files with size 0 are considered corrupted
                if file_size == 0:
                    validation_status = "Corrupted"
                    manifest["Summary"]["Corrupted"] += 1

                    errors = manifest.setdefault("Media_Errors", {
                        "Missing Files": [],
                        "Corrupted Files": []
                    })
                    errors["Corrupted Files"].append(media_file_path)
                else:
                    # Successfully validated media file
                    manifest["Summary"]["Media"] += 1

            except OSError as e:
                msg: str = (f"Media missing for {media_file_path}: {e}")

                # If the media file is missing, mark it as such and add to the
                # manifest, but continue processing other files
                validation_status: str = "Missing"
                manifest["Summary"]["Missing"] += 1

                errors = manifest.setdefault("Media_Errors", {
                    "Missing Files": [],
                    "Corrupted Files": []
                })
                errors["Missing Files"].append(msg)
                continue

            # Track duplicates based on file name and size
            duplicate_key: Tuple = (media_file_name, file_size)
            if duplicate_key in duplicate_tracker:
                duplicate_tracker[duplicate_key].append(
                    (media_file_path, download_url))
                # Skip adding duplicate records to the manifest until we
                # process all files
                continue

            else:
                duplicate_tracker[duplicate_key] = [
                    (media_file_path, download_url)]

            # Build the record for the manifest
            record: Tuple = (
                media_file_name,
                file_size,
                timestamp,
                validation_status
            )

            media_items.append(record)

    # Sort media items by timestamp oldest to newest
    media_items.sort(key=lambda x: x[2]) 

    for item in media_items:
        file_name, file_size, timestamp, validation_status = item
        paths_and_downloads: List = duplicate_tracker.get(
            (file_name, file_size),
            [])

        instances = []
        for path, download in paths_and_downloads:
            instances.append({
                "path": path,
                "download_url": download
            })

        # Count duplicates beyond the first occurrence
        manifest["Summary"]["Duplicates"] += len(paths_and_downloads) - 1
        manifest["Summary"]["Unique"] += 1

        manifest["Manifest"].append({
            "file_name": file_name,
            "file_size": file_size,
            "timestamp": timestamp,
            "validation_status": validation_status,
            "instances": instances,
        })

    # Generate a timestamped manifest file name and save the manifest as JSON
    manifestFileName = f'manifest_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'

    with open(manifestFileName, 'w') as f:
        try:
            json.dump(manifest, f, indent=4)
        except Exception as e:
            print(f"Error saving manifest file {manifestFileName}: {e}")

    return manifestFileName


def pp_manifest(manifest_name: str) -> None:
    '''Pretty print the Manifest file'''

    with open(manifest_name, 'r') as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding manifest file {manifest_name}: {e}")
            return

    for category, result in manifest["Summary"].items():
        print(f"{category}: {result}")

    if manifest.get("Media_Errors"):
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
        description='''Validate Google Takeout media JSON and generate a
            manifest.'''
    )
    parser.add_argument(
        '--media-root',
        default='.',
        help='Path to the root directory containing the media and JSON files.')
    args = parser.parse_args()

    print(f"Validating media in root directory: {args.media_root}")

    manifest_name = generate_manifest(args.media_root)
    pp_manifest(manifest_name)


if __name__ == "__main__":
    print("This is the validator module.")
    main()
