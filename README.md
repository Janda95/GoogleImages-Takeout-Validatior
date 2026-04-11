# GoogleImages-Takeout-Validatior
A validation script to setup and compare local manifests to images backup downloaded using the GoogleTakeout service.

### Why:
Unfortunately there is no simple way to download or query for a manifest for Google Photos against GoogleTakeout. This python script will walk through a directory tree and build a manifest for local verification.

### How to setup:



### How to download data:
1. [Google Takeout](https://takeout.google.com/)
1. Request data for google photos
    - Note: 2gb will split zip files into 2gb zip files, larger zip files should be fine for any machine not running an older OS.
1. Extract via link sent to Email
1. Download all zip files
1. Extract and merge to consolidated location so all files live together in a unique shared directory

### Running the Script:



### Output --- Json
~~~ 
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
~~~

### Manifest Comparison Options
1. Confirm files are intact with generated JSON
1. Spot check with expected file count in Google Photos GUI
1. Download and consolidate data again a few days apart and compare generated JSON against the other
