import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from mutagen import File


def parse_and_clean_artists(artist_tag):
  if not artist_tag:
    return "", ""

  artist_tag = artist_tag.strip("; ").strip()

  # 1. Check for explicit featuring keywords
  feat_match = re.search(
      r"\b(feat\.?|ft\.?|featuring)\b", artist_tag, re.IGNORECASE
  )
  if feat_match:
    idx = feat_match.start()
    main_artist = artist_tag[:idx].strip(" ,;-")
    featured_artists = artist_tag[idx:].strip()
    featured_artists = re.sub(
        r"\b(feat\.?|ft\.?|featuring)\b",
        "feat.",
        featured_artists,
        flags=re.IGNORECASE,
    )
    return main_artist, featured_artists

  # 2. Handle comma- or semicolon-separated lists
  if "," in artist_tag or ";" in artist_tag:
    parts = re.split(r"[,;]", artist_tag)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) > 1:
      main_artist = parts[0]
      feat_list = ", ".join(parts[1:])
      return main_artist, f"feat. {feat_list}"

  return artist_tag, ""


class TaggerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Universal Audio Artist & Title Tagger")
    self.root.geometry("600x400")

    # Instruction Label
    self.label = tk.Label(
        root,
        text="Click below to choose your music library folder:",
        font=("Arial", 11),
    )
    self.label.pack(pady=10)

    # Browse Button
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

    # Status / Output Log Text Box
    self.log_area = scrolledtext.ScrolledText(
        root, wrap=tk.WORD, width=70, height=15, font=("Consolas", 9)
    )
    self.log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    self.log_area.insert(
        tk.END,
        "Ready. Supports MP3, FLAC, M4A, OGG, WAV, AAC, and more.\n",
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

    # Run in a separate thread so the GUI doesn't freeze
    threading.Thread(
        target=self.process_files, args=(folder_path,), daemon=True
    ).start()

  def process_files(self, folder_path):
    # Supported audio extensions
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
      # easy=True standardizes tag keys across MP3, FLAC, M4A, OGG, etc.
      audio = File(file_path, easy=True)
      if audio is None:
        return False
    except Exception:
      return False

    # Extract artist safely
    artist_list = audio.get("artist", [])
    if not artist_list:
      return False
    artist_str = (
        artist_list[0] if isinstance(artist_list, list) else str(artist_list)
    )

    main_artist, feat_str = parse_and_clean_artists(artist_str)
    if not main_artist:
      return False

    # Extract title safely
    title_list = audio.get("title", [])
    title_str = (
        title_list[0]
        if (isinstance(title_list, list) and title_list)
        else str(title_list)
    )

    updated = False

    # Cleanly append featuring artists to title if found and not already present
    if feat_str and feat_str.lower() not in title_str.lower():
      new_title = f"{title_str} ({feat_str})" if title_str else feat_str
      audio["title"] = [new_title]
      updated = True

    # Strip supporting artists out of the primary Artist field, leaving only the main artist
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
