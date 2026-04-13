# GoogleImages-Takeout-Validatior
A validation script to setup and compare local manifests to images backup downloaded using the GoogleTakeout service.

### Why:
Unfortunately there is no simple way to download or query for a manifest for Google Photos against GoogleTakeout. Use this script to generate a manifest which is made by walking through a directory tree, checking for both metadata json and its associated media, providing insight on downloaded Takeout request. 

### Step 1: Data Download and Preperation
1. [Google Takeout](https://takeout.google.com/)
1. Request data for google photos
    - Note: 2gb will split zip files into 2gb zip files, larger zip files should be fine for any machine not running an older OS.
1. Extract via link sent to Email
1. Download all zip files
1. Extract and merge to consolidated location so all files live together in a unique shared directory
    - Note: In the case where you are downloading more than one zip file, if they are not consolidated and merged, the manifest will likely reflect there is missing media. By default there is no gaurantee the json and media files live in the same downloaded zip file and could to be spread out across zip files.


### Running the Script:

```bash
python3 validator.py --media-root <path/to/root>
```
If `media-root` flag is ommited, defaults to `./`

This script walks through a consolidated Takeout tree, validates each `supplemental-metada.json` file against its media, and writes a timestamped manifest JSON file.

### JSON Output Example:

This example shows the optimal output when no media files are missing or corrupted.
~~~json
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
            "validation_status": "Valid",
            "instances": [
                {
                    "path": "/root/GoogleTakeout/Photos/photo1.jpg",
                    "download_url": "https://<photos.google.com>/photo1.jpg"
                }
            ]
        },
        {
            "file_name": "photo2.jpg",
            "file_size": 654321,
            "timestamp": "1672531300",
            "validation_status": "Duplicate",
            "instances": [
                {
                    "path": "/root/GoogleTakeout/Photos/photo2.jpg",
                    "download_url": "https://<photos.google.com>/photo2.jpg"
                },
                {
                    "path": "/root/GoogleTakeout/Photos/Copy/photo2.jpg",
                    "download_url": "https://<photos.google.com>/photo2.jpg"
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

### Manifest Comparison Options:
1. Confirm files are intact with generated JSON
1. Spot check with expected file count in Google Photos GUI
1. Download and consolidate data again a few days apart and compare generated JSON against the other
