# Contributing-Artist-Tag-Remover
A Python desktop utility designed to clean up messy ID3 tags in large MP3 music libraries. It automatically parses complex artist fields (containing multiple artists separated by commas, semicolons, or featuring keywords), isolates the primary main artist, and neatly appends any secondary artists into the song title as `(feat. ...)`.
## Features
* **Smart Artist Parsing:** Handles comma-separated lists (e.g., `A$AP Rocky, ScHoolboy Q`), semicolon lists, and explicit keywords (`feat.`, `ft.`, `featuring`).
* **Tag Restructuring:** Safely updates the primary Artist (`TPE1`) tag to just the main artist, and updates the Title (`TIT2`) tag to include featuring artists without duplicating tags.
* **Graphical User Interface (GUI):** Features a Tkinter window with live operation logs.
* **Support for file types:** MP3, FLAC, M4A, OGG, WAV, and AAC files.

## Requirements
* **Python 3.x**
* **Mutagen Library** (for ID3 tag manipulation)

## Installation & Setup

1. Clone or download this repository.
   ```cmd
   git clone [https://github.com/ColoradoCrusade/Contributing-Artist-Tag-Remover.git](https://github.com/ColoradoCrusade/Contributing-Artist-Tag-Remover.git)
2. Install the required Python package via your command line:
   ```cmd
   pip install mutagen
3. Execute the script from your terminal:
   ```cmd
   python "contributingArtistTagRemover.py"
## Usage
1. Click the "Select Music Folder & Start" button in the graphical window.
2. Choose your root music library directory.
3. Watch the live log as it cleans and saves your tags.

# Always back up your files before batch operations!
