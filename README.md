# SC-Asset-Downloader

File downloader for SC assets. Downloads the latest game data directly from servers.

## Supported
- Clash Royale PROD

## Usage

Python ≥ 3.9

Do `pip install -r requirements.txt` then run `!run.bat`

## Features

Features added in this fork include:

1. Quicker Version Detection
2. Integrated Decompression

## Flags

* `--hash`
  Download assets directly using a version hash. Assets are saved into a folder named after the hash.
  Example:

  ```bash
  py main.py --hash=SomeVersionHash
  ```

* `--repair-mode`
  Checks only for missing files and downloads them. Useful if you already unpacked game assets and need only the missing ones.

* `--strict-repair-mode`
  Verifies files by content hash and restores corrupted or modified files. Slower but ensures correctness.

## Patches

Generates patches between two versions.
Copies new and changed files into:

```
patches/{Server}/{old_version} {new_version}/
```

If `make_detailed_patches` is enabled in `config.json`, the patch is divided into:

* New files
* Changed files
* Deleted files

## Config (`config.json`)

* `servers` — dictionary of server names and their addresses.
* `auto_update` — automatically update when new files are available.
* `make_patches`, `make_detailed_patches` — patch generation settings.
* `max_workers` — maximum number of concurrent threads.
* `worker_max_items` — maximum items per worker thread.
* `save_dump` — debug option for saving raw server responses.
