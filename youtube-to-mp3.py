import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import yt_dlp

def download_youtube_mp3(url, output_dir, progress_callback):
    # 確保目錄存在
    os.makedirs(output_dir, exist_ok=True)

    def progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                progress = int(downloaded_bytes / total_bytes * 100)
                progress_callback(progress)

    # yt-dlp 設定
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [progress_hook],
        # 'ffmpeg_location': r'C:\ffmpeg\bin',  # 你的 ffmpeg 路徑
    }


    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_audio():
    url = url_entry.get()
    output_dir = output_dir_var.get()

    if not url.strip():
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return

    if not output_dir:
        messagebox.showerror("Error", "Please select an output directory.")
        return

    try:
        progress_var.set(0)
        download_youtube_mp3(url, output_dir, update_progress)
        messagebox.showinfo("Success", "Download and conversion completed!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def select_output_dir():
    directory = filedialog.askdirectory()
    if directory:
        output_dir_var.set(directory)

def update_progress(progress):
    progress_var.set(progress)
    root.update_idletasks()

# Create the main window
root = tk.Tk()
root.title("YouTube to MP3 Converter")
root.geometry("400x250")

# URL entry
url_label = tk.Label(root, text="YouTube URL:")
url_label.pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

# Output directory selection
output_dir_var = tk.StringVar()
output_dir_label = tk.Label(root, text="Output Directory:")
output_dir_label.pack(pady=5)
output_dir_frame = tk.Frame(root)
output_dir_frame.pack(pady=5)
output_dir_entry = tk.Entry(output_dir_frame, textvariable=output_dir_var, width=35)
output_dir_entry.pack(side=tk.LEFT, padx=5)
output_dir_button = tk.Button(output_dir_frame, text="Browse", command=select_output_dir)
output_dir_button.pack(side=tk.LEFT)

# Progress bar
progress_var = tk.IntVar()
progress_bar = tk.ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(pady=10, fill=tk.X, padx=20)

# Download button
download_button = tk.Button(root, text="Download MP3", command=download_audio)
download_button.pack(pady=20)

# Start the GUI loop
root.mainloop()
