# Version 1.1
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from mutagen import File


def parse_and_clean_artists(artist_tag, album_artist_tag=""):
  if not artist_tag:
    return "", ""

  clean_tag = artist_tag.strip("; ").strip()
  clean_album_artist = (
      album_artist_tag.strip("; ").strip() if album_artist_tag else ""
  )

  # DYNAMIC PROTECTION:
  # If the Album Artist exists, has an '&', and matches the start of the track artist
  # (or equals it), treat that base name as a single protected artist entity.
  if clean_album_artist and "&" in clean_album_artist:
    if clean_tag.lower() == clean_album_artist.lower():
      return clean_tag, ""
    # Handle cases where track artist has a feature added to the album artist
    if clean_tag.lower().startswith(clean_album_artist.lower()):
      # Extract whatever is trailing after the album artist name
      remainder = clean_tag[len(clean_album_artist) :].strip(" ,;-&")
      if remainder:
        # Check if remainder already has feat syntax
        if not re.search(
            r"\b(feat\.?|ft\.?|featuring)\b", remainder, re.IGNORECASE
        ):
          remainder = f"feat. {remainder}"
        return clean_album_artist, remainder
      return clean_tag, ""

  # 1. Check for explicit featuring keywords
  feat_match = re.search(
      r"\b(feat\.?|ft\.?|featuring)\b", clean_tag, re.IGNORECASE
  )
  if feat_match:
    idx = feat_match.start()
    main_artist = clean_tag[:idx].strip(" ,;-")
    featured_artists = clean_tag[idx:].strip()
    featured_artists = re.sub(
        r"\b(feat\.?|ft\.?|featuring)\b",
        "feat.",
        featured_artists,
        flags=re.IGNORECASE,
    )
    return main_artist, featured_artists

  # 2. Handle comma, semicolon, or '&' separated collaborations (e.g., "Bones & Cat Soup")
  if "," in clean_tag or ";" in clean_tag or "&" in clean_tag:
    parts = re.split(r"[,;]|\s+&\s+", clean_tag)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) > 1:
      main_artist = parts[0]
      feat_list = ", ".join(parts[1:])
      return main_artist, f"feat. {feat_list}"

  return clean_tag, ""


class TaggerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Universal Audio Artist & Title Tagger (Dynamic)")
    self.root.geometry("600x450")

    self.label = tk.Label(
        root,
        text=(
            "Click below to choose your music library folder:\n(Uses Album"
            " Artist tags to protect band names with '&')"
        ),
        font=("Arial", 11),
    )
    self.label.pack(pady=10)

    self.btn_browse = tk.Button(
        root,
        text="Select Music Folder & Start",
        font=("Arial", 11, "bold"),
        bg="#4CAF50",
        fg="white",
        padx=10,
        pady=5,
        command=self.start_processing,
    )
    self.btn_browse.pack(pady=5)

    self.log_area = scrolledtext.ScrolledText(
        root, wrap=tk.WORD, width=70, height=15, font=("Consolas", 9)
    )
    self.log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    self.log_area.insert(
        tk.END,
        "Ready. Dynamic Album Artist checking is active.\n",
    )

  def log(self, message):
    self.log_area.insert(tk.END, message + "\n")
    self.log_area.see(tk.END)

  def start_processing(self):
    folder_path = filedialog.askdirectory(
        title="Select Music Folder to Process"
    )
    if not folder_path:
      return

    self.btn_browse.config(state=tk.DISABLED)
    self.log(f"\n--- Starting scan in: {folder_path} ---")

    threading.Thread(
        target=self.process_files, args=(folder_path,), daemon=True
    ).start()

  def process_files(self, folder_path):
    audio_extensions = (".mp3", ".flac", ".m4a", ".ogg", ".wav", ".aac", ".opus")
    processed_count = 0
    file_count = 0

    for root_dir, _, files in os.walk(folder_path):
      for file in files:
        if file.lower().endswith(audio_extensions):
          file_count += 1
          full_path = os.path.join(root_dir, file)
          if self.process_single_file(full_path):
            processed_count += 1
            self.log(f"Updated: {file}")

    self.log(
        f"\n--- Complete! Scanned {file_count} audio files. Updated"
        f" {processed_count} files. ---"
    )
    messagebox.showinfo(
        "Finished", f"Successfully processed {processed_count} files!"
    )
    self.btn_browse.config(state=tk.NORMAL)

  def process_single_file(self, file_path):
    try:
      audio = File(file_path, easy=True)
      if audio is None:
        return False
    except Exception:
      return False

    # Get track artist
    artist_list = audio.get("artist", [])
    if not artist_list:
      return False
    artist_str = (
        artist_list[0] if isinstance(artist_list, list) else str(artist_list)
    )

    # Get album artist (if available) to cross-reference band names safely
    album_artist_list = audio.get("albumartist", [])
    album_artist_str = (
        album_artist_list[0]
        if (isinstance(album_artist_list, list) and album_artist_list)
        else str(album_artist_list)
    )

    main_artist, feat_str = parse_and_clean_artists(
        artist_str, album_artist_str
    )
    if not main_artist:
      return False

    title_list = audio.get("title", [])
    title_str = (
        title_list[0]
        if (isinstance(title_list, list) and title_list)
        else str(title_list)
    )

    updated = False

    if feat_str and feat_str.lower() not in title_str.lower():
      new_title = f"{title_str} ({feat_str})" if title_str else feat_str
      audio["title"] = [new_title]
      updated = True

    if main_artist != artist_str:
      audio["artist"] = [main_artist]
      updated = True

    if updated:
      audio.save()
      return True
    return False


if __name__ == "__main__":
  root = tk.Tk()
  app = TaggerApp(root)
  root.mainloop()
