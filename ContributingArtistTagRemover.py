import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from mutagen.id3 import ID3, ID3NoHeaderError, TPE1, TIT2


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
    self.root.title("MP3 Artist & Title Tagger")
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
        tk.END, "Ready. Click the button above to begin processing.\n"
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
    processed_count = 0
    file_count = 0

    for root_dir, _, files in os.walk(folder_path):
      for file in files:
        if file.lower().endswith(".mp3"):
          file_count += 1
          full_path = os.path.join(root_dir, file)
          if self.process_single_file(full_path):
            processed_count += 1
            self.log(f"Updated: {file}")

    self.log(
        f"\n--- Complete! Scanned {file_count} MP3 files. Updated"
        f" {processed_count} files. ---"
    )
    messagebox.showinfo(
        "Finished", f"Successfully processed {processed_count} files!"
    )
    self.btn_browse.config(state=tk.NORMAL)

  def process_single_file(self, file_path):
    try:
      audio = ID3(file_path)
    except (ID3NoHeaderError, Exception):
      return False

    artist_str = ""
    if "TPE1" in audio:
      artist_str = str(audio["TPE1"])

    main_artist, feat_str = parse_and_clean_artists(artist_str)
    if not main_artist:
      return False

    title_str = ""
    if "TIT2" in audio:
      title_str = str(audio["TIT2"])

    updated = False

    if feat_str and feat_str.lower() not in title_str.lower():
      new_title = f"{title_str} ({feat_str})"
      audio["TIT2"] = TIT2(encoding=3, text=new_title)
      updated = True

    if main_artist != artist_str:
      audio["TPE1"] = TPE1(encoding=3, text=main_artist)
      updated = True

    if updated:
      audio.save()
      return True
    return False


if __name__ == "__main__":
  root = tk.Tk()
  app = TaggerApp(root)
  root.mainloop()