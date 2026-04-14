# GoogleImages-Takeout-Validatior
A validation script to setup and compare local manifests to images backup downloaded using the GoogleTakeout service.

### Why
Google Takeout can be difficult to audit because it exports metadata and media files without a single unified manifest. This tool is intended to walk through the consolidated folder structure, validate each `supplemental-metada.json` entry against its corresponding media file, and produce an overall summary of files found. The manifest includes tracking json/media pairs, missing and corrupted media, and duplicate file directory and url locations and is sorted by timestamps based on when the picuture was taken.

### Data Download and Preparation
- Visit [Google Takeout](https://takeout.google.com/)
- Request data for Google Photos
  - Note: exports larger than 2GB are split into multiple 2GB zip files.
- Download every generated archive file
- Extract each zip archive
- Consolidate all extracted folders into a single shared root directory
  - Important: if the extracted data is left split across multiple exports, `supplemental-metada.json` files and their corresponding media may end up in separate packages, causing the manifest to report missing media.


### Running the Script:

```bash
python3 validator.py --media-root <path/to/root>
```
If the `--media-root` flag is omitted, it defaults to the current working directory (`./`).

This script recursively searches the provided root for `*supplemental-metada.json` files, validates each JSON record against its associated media file, and writes a timestamped manifest JSON file.

The generated manifest includes a `Summary`, a `Manifest` list with `instance_status`, and optional `Media_Errors` when missing or corrupted media is detected.

### JSON Output Example:

This example shows the optimal output when no media files are missing or corrupted.
~~~json
manifest_timestamp.json

{
    "Summary": {
        "JSON": 1209,
        "Media": 1209,
        "Unique": 574,
        "Duplicates": 635,
        "Corrupted": 0,
        "Missing": 0
    },
    "Manifest": [
        {
            "file_name": "photo1.jpg",
            "file_size": 123456,
            "timestamp": "1672531200",
            "instance_status": "Single",
            "instances": [
                {
                    "path": "/root/GoogleTakeout/Photos/photo1.jpg",
                    "download_url": "https://<photos.google.com>/photo1.jpg",
                    "validation_status": "Valid"
                }
            ]
        },
        {
            "file_name": "photo2.jpg",
            "file_size": 654321,
            "timestamp": "1672531300",
            "instance_status": "Multiple",
            "instances": [
                {
                    "path": "/root/GoogleTakeout/Photos/photo2.jpg",
                    "download_url": "https://<photos.google.com>/photo2.jpg",
                    "validation_status": "Valid"
                },
                {
                    "path": "/root/GoogleTakeout/Photos/Copy/photo2.jpg",
                    "download_url": "https://<photos.google.com>/photo2.jpg",
                    "validation_status": "Valid"
                }
            ]
        }
    ]
}
~~~

If errors are detected, the generated manifest will also include:
~~~json
"Media_Errors": {
  "Missing Files": [
    "/path/to/missing/file1.jpg"
  ],
  "Corrupted Files": [
    "/path/to/corrupted/file2.jpg"
  ]
}
~~~

### Manifest Comparison Options

| What to compare | Why it matters | How to do it |
|---|---|---|
| `Summary` totals | Ensures the export is complete | Read the top-level counts |
| `Unique` vs `Duplicates` | Reflects duplicate export behavior | Count `Multiple` entries |
| `Media_Errors` | Finds missing/corrupted items | Review listed file paths |
| Multiple manifests | Tracks differences across exports | Use `diff` / `jq` |

### Notes about Google Takeout behavior
- Google Takeout frequently produces duplicate media entries because it exports every version, edits, and duplicate file copies it finds in your account or album structure.
- Takeout does not always preserve a single, consistent folder layout: the same photo may appear in multiple export folders, or a JSON metadata file may refer to a media file that is duplicated elsewhere.
- If you export from multiple Takeout archives and then merge them manually, duplicates are common because the same image can exist in more than one archive package.
- Missing files can occur when metadata and media are split across different zip exports, so consolidating all extracted folders before validation is important.
- Corrupted files are usually zero-byte placeholders or incomplete downloads rather than actual image corruption in Google Photos.
