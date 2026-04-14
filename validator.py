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


def scan_and_validate(media_root: str) -> Tuple[List[Dict], Dict[str, List[str]], Dict[str, int]]:
    '''Scan the media root, validate each JSON record, and return raw records,
    errors, and summary counts.'''

    records: List[Dict] = []
    errors: Dict[str, List[str]] = {}
    summary = {
        "JSON": 0,
        "Media": 0,
        "Unique": 0,
        "Duplicates": 0,
        "Corrupted": 0,
        "Missing": 0
    }

    for root, dirs, files in os.walk(Path(media_root), topdown=True):
        root_path = Path(root)
        for file in files:
            if not file.endswith('supplemental-metada.json'):
                continue

            json_path = root_path / file
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    json_file = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON file {json_path}: {e}")
                    continue

            summary["JSON"] += 1

            # Extract required fields with error handling
            try:
                media_file_name = json_file["title"]
                download_url = json_file.get("url", "")
                photo_taken_time = json_file.get("photoTakenTime", {})
                timestamp = photo_taken_time.get("timestamp", "")
            except KeyError as e:
                print(f"Error parsing JSON file {json_path}: missing {e}")
                continue

            media_file_path = root_path / media_file_name
            validation_status = "Valid"
            file_size = 0

            # Validate media file existence and size
            try:
                file_size = getsize(media_file_path)
                if file_size == 0:
                    validation_status = "Corrupted"
                    summary["Corrupted"] += 1
                    corrupted = errors.setdefault("Corrupted Files", [])
                    corrupted.append(str(media_file_path))
                else:
                    summary["Media"] += 1
            except OSError as e:
                validation_status = "Missing"
                summary["Missing"] += 1
                missing = errors.setdefault("Missing Files", [])
                missing.append(f"Media missing for {media_file_path}: {e}")
                continue

            records.append({
                "file_name": media_file_name,
                "file_size": file_size,
                "timestamp": timestamp,
                "validation_status": validation_status,
                "path": str(media_file_path),
                "download_url": download_url
            })

    return records, errors, summary


def track_duplicates(records: List[Dict]) -> Dict[Tuple[str, int], List[Dict]]:
    '''Group validated records by (file_name, file_size) for duplicate tracking.'''

    duplicate_groups: Dict[Tuple[str, int], List[Dict]] = defaultdict(list)
    for record in records:
        key = (record["file_name"], record["file_size"])
        duplicate_groups[key].append({
            "path": record["path"],
            "download_url": record["download_url"],
            "validation_status": record["validation_status"],
        })

    return duplicate_groups


def build_manifest_payload(
    records: List[Dict],
    duplicate_groups: Dict[Tuple[str, int], List[Dict]],
    errors: Dict[str, List[str]],
    summary: Dict[str, int]
) -> Dict:
    '''Build the final JSON payload for the manifest file.'''

    payload = {
        "Summary": summary.copy(),
        "Manifest": []
    }

    seen_keys = set()
    for record in records:
        key = (record["file_name"], record["file_size"])
        if key in seen_keys:
            continue

        seen_keys.add(key)
        instances = duplicate_groups.get(key, [
            {
                "path": record["path"],
                "download_url": record["download_url"]
            }
        ])

        if len(instances) > 1:
            payload["Summary"]["Duplicates"] += len(instances) - 1
            validation_status = "Duplicate"
        else:
            validation_status = record["validation_status"]

        payload["Summary"]["Unique"] += 1

        payload["Manifest"].append({
            "file_name": record["file_name"],
            "file_size": record["file_size"],
            "timestamp": record["timestamp"],
            "validation_status": validation_status,
            "instances": instances
        })

    if errors:
        payload["Media_Errors"] = errors

    return payload


def save_manifest(payload: Dict) -> str:
    '''Save the manifest payload to a timestamped JSON file.'''

    manifest_file_name = f"manifest_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(manifest_file_name, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=4)
    return manifest_file_name


def scan_and_save_manifest(media_root: str) -> str:
    records, errors, summary = scan_and_validate(media_root)
    duplicate_groups = track_duplicates(records)
    payload = build_manifest_payload(records, duplicate_groups, errors, summary)
    return save_manifest(payload)


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
        if manifest["Media_Errors"].get("Missing Files"):
            print("\nMissing Files:")
            for missing in manifest["Media_Errors"]["Missing Files"]:
                print(f"  - {missing}")

        if manifest["Media_Errors"].get("Corrupted Files"):
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

    manifest_name = scan_and_save_manifest(args.media_root)
    pp_manifest(manifest_name)


if __name__ == "__main__":
    print("This is the validator module.")
    main()
