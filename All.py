
from flask import Flask, render_template_string, request, send_file, redirect, url_for, jsonify
import yt_dlp
import os
import uuid
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC, TALB, error
import requests
from datetime import datetime
import re
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
    <title>Areszyn Music Downloader Pro</title>
    <meta property="og:title" content="Areszyn" />
    <meta property="og:description" content="Download high quality YouTube music with metadata, cover art and multiple format options." />
    <meta property="og:image" content="https://envs.sh/YTD.jpg" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #8a2be2;
            --secondary: #9370db;
            --accent: #ff6f61;
            --success: #38b000;
            --dark: #1a1a2e;
            --light: #f8f9fa;
            --gray: #6c757d;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--dark), #16213e);
            color: var(--light);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.6;
        }

        header {
            padding: 1.5rem;
            text-align: center;
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            user-select: none;
        }

        .logo i {
            color: var(--accent);
        }

        nav {
            display: flex;
            gap: 1.5rem;
        }

        nav a {
            color: var(--light);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        nav a:hover {
            color: var(--accent);
        }

        main {
            flex-grow: 1;
            padding: 2rem 1rem;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }

        .hero {
            text-align: center;
            padding: 3rem 1rem;
            margin-bottom: 2rem;
        }

        .hero h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(to right, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero p {
            font-size: 1.1rem;
            max-width: 700px;
            margin: 0 auto 2rem;
            color: rgba(255, 255, 255, 0.8);
        }

        .search-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        .input-group {
            display: flex;
            gap: 0.5rem;
        }

        input[type="text"], input[type="url"], select {
            flex-grow: 1;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: var(--light);
            font-size: 1rem;
            transition: all 0.3s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(138, 43, 226, 0.3);
        }

        .btn {
            background: var(--accent);
            border: none;
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn:hover {
            background: #ff4a3d;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 111, 97, 0.4);
        }

        .btn i {
            font-size: 1.1rem;
        }

        .btn-secondary {
            background: var(--secondary);
        }

        .btn-secondary:hover {
            background: #7b5dd6;
            box-shadow: 0 5px 15px rgba(147, 112, 219, 0.4);
        }

        .btn-success {
            background: var(--success);
        }

        .btn-success:hover {
            background: #2a8a00;
            box-shadow: 0 5px 15px rgba(56, 176, 0, 0.4);
        }

        .preview {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .preview img {
            max-width: 250px;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s;
        }

        .preview img:hover {
            transform: scale(1.05);
        }

        .preview h2 {
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: white;
        }

        .preview p {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: rgba(255, 255, 255, 0.8);
        }

        .preview .metadata {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 1.5rem 0;
            flex-wrap: wrap;
        }

        .metadata-item {
            background: rgba(0, 0, 0, 0.3);
            padding: 0.75rem 1.5rem;
            border-radius: 2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .metadata-item i {
            color: var(--primary);
        }

        audio {
            width: 100%;
            max-width: 500px;
            margin: 1.5rem auto;
            border-radius: 0.5rem;
            outline: none;
        }

        .download-options {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 2rem;
        }

        .download-btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--success);
            color: white;
            padding: 0.9rem 1.8rem;
            border-radius: 0.75rem;
            font-weight: 600;
            text-decoration: none;
            user-select: none;
            transition: all 0.3s;
        }

        .download-btn:hover {
            background: #2a8a00;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(56, 176, 0, 0.4);
        }

        .back-btn {
            display: inline-block;
            margin-top: 2rem;
            color: var(--gray);
            text-decoration: none;
            transition: color 0.3s;
        }

        .back-btn:hover {
            color: var(--accent);
        }

        .error {
            background: rgba(255, 68, 68, 0.8);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            animation: shake 0.5s;
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-5px); }
            40%, 80% { transform: translateX(5px); }
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 1rem;
            padding: 2rem;
            transition: all 0.3s;
        }

        .feature-card:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-5px);
        }

        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: var(--primary);
        }

        .feature-card h3 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .feature-card p {
            color: rgba(255, 255, 255, 0.7);
        }

        footer {
            text-align: center;
            padding: 2rem;
            background: rgba(0, 0, 0, 0.3);
            margin-top: auto;
        }

        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
        }

        .social-links {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin: 1rem 0;
        }

        .social-links a {
            color: var(--light);
            font-size: 1.5rem;
            transition: color 0.3s;
        }

        .social-links a:hover {
            color: var(--accent);
        }

        .copyright {
            color: var(--gray);
            font-size: 0.9rem;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 1rem;
            }

            nav {
                gap: 1rem;
            }

            .hero h1 {
                font-size: 2rem;
            }

            .input-group {
                flex-direction: column;
            }

            .btn {
                width: 100%;
                justify-content: center;
            }
        }

        /* Loading spinner */
        .spinner {
            display: none;
            width: 40px;
            height: 40px;
            margin: 1rem auto;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid var(--accent);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Lyrics section */
        .lyrics-container {
            margin-top: 2rem;
            text-align: left;
            background: rgba(0, 0, 0, 0.2);
            padding: 1.5rem;
            border-radius: 0.75rem;
            max-height: 300px;
            overflow-y: auto;
        }

        .lyrics-container h3 {
            margin-bottom: 1rem;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .lyrics {
            white-space: pre-line;
            line-height: 1.8;
        }

        /* Playlist support */
        .playlist-info {
            margin-top: 1.5rem;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 0.5rem;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="logo">
                <i class="fas fa-music"></i>
                <span>Areszyn Music</span>
            </div>
            <nav>
                <a href="#features"><i class="fas fa-star"></i> Features</a>
                <a href="#how-it-works"><i class="fas fa-question-circle"></i> How It Works</a>
                <a href="https://github.com/GitHub"  target="_blank"><i class="fab fa-github"></i> GitHub</a>
            </nav>
        </div>
    </header>

    <main>
        <section class="hero">
            <h1>Download High Quality Music</h1>
            <p>Convert YouTube videos to MP3 with metadata, album art, and lyrics support. Fast, secure, and free!</p>
        </section>

        <section class="search-container">
            {% if error %}
                <div class="error">
                    <i class="fas fa-exclamation-circle"></i>
                    {{ error }}
                </div>
            {% endif %}

            {% if not preview %}
                <form id="download-form" method="POST" autocomplete="off" spellcheck="false">
                    <div class="form-group">
                        <label for="url"><i class="fas fa-link"></i> YouTube Music URL</label>
                        <div class="input-group">
                            <input type="url" name="url" id="url" placeholder="Paste YouTube music video or playlist link here..." required autofocus />
                            <button type="submit" class="btn">
                                <i class="fas fa-search"></i> Fetch
                            </button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="format"><i class="fas fa-file-audio"></i> Audio Format</label>
                        <select name="format" id="format">
                            <option value="mp3">MP3 (Standard Quality)</option>
                            <option value="mp3_high">MP3 (High Quality 320kbps)</option>
                            <option value="flac">FLAC (Lossless)</option>
                            <option value="m4a">M4A (AAC)</option>
                            <option value="opus">Opus (Efficient)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label><i class="fas fa-sliders-h"></i> Options</label>
                        <div style="display: flex; gap: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem;">
                                <input type="checkbox" name="add_metadata" checked />
                                Add Metadata
                            </label>
                            <label style="display: flex; align-items: center; gap: 0.5rem;">
                                <input type="checkbox" name="add_lyrics" />
                                Search for Lyrics
                            </label>
                        </div>
                    </div>
                </form>

                <div class="spinner" id="loading-spinner"></div>
            {% else %}
                <div class="preview">
                    <img src="{{ thumbnail }}" alt="Cover Art" loading="lazy" />
                    <h2>{{ title }}</h2>
                    <p>{{ artist }}</p>

                    <div class="metadata">
                        <div class="metadata-item">
                            <i class="fas fa-clock"></i>
                            <span>{{ duration }}</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-headphones"></i>
                            <span>{{ quality }}</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-download"></i>
                            <span>{{ size }}</span>
                        </div>
                    </div>

                    <audio controls preload="none" src="{{ audio_url }}"></audio>

                    {% if lyrics %}
                        <div class="lyrics-container">
                            <h3><i class="fas fa-align-left"></i> Lyrics</h3>
                            <div class="lyrics">{{ lyrics }}</div>
                        </div>
                    {% endif %}

                    {% if playlist %}
                        <div class="playlist-info">
                            <p><i class="fas fa-list"></i> This track is part of a playlist: <strong>{{ playlist.title }}</strong> ({{ playlist.count }} tracks)</p>
                        </div>
                    {% endif %}

                    <div class="download-options">
                        <a href="{{ audio_url }}" class="download-btn" download="{{ filename }}">
                            <i class="fas fa-download"></i> Download MP3
                        </a>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">
                            <i class="fas fa-redo"></i> Convert Another
                        </a>
                    </div>
                </div>
            {% endif %}
        </section>

        {% if not preview %}
            <section id="features" class="features">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-tags"></i>
                    </div>
                    <h3>Metadata Included</h3>
                    <p>All downloads include proper ID3 tags with title, artist, album, and cover art embedded directly in the audio file.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-music"></i>
                    </div>
                    <h3>Multiple Formats</h3>
                    <p>Choose from various audio formats including MP3, FLAC, M4A, and Opus to suit your quality and size preferences.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-bolt"></i>
                    </div>
                    <h3>Fast Processing</h3>
                    <p>Our optimized servers ensure quick conversion and downloading, even for high-quality audio files.</p>
                </div>
            </section>

            <section id="how-it-works" class="feature-card">
                <h2><i class="fas fa-question-circle"></i> How It Works</h2>
                <ol style="padding-left: 1.5rem; margin-top: 1rem;">
                    <li style="margin-bottom: 0.5rem;">Paste a YouTube music video URL in the input field above</li>
                    <li style="margin-bottom: 0.5rem;">Select your preferred audio format and options</li>
                    <li style="margin-bottom: 0.5rem;">Click "Fetch" to retrieve the music details</li>
                    <li style="margin-bottom: 0.5rem;">Preview the track and click "Download" to save it</li>
                </ol>
                <p style="margin-top: 1rem;"><i class="fas fa-info-circle"></i> Note: This service is for personal use only. Please respect copyright laws.</p>
            </section>
        {% endif %}
    </main>

    <footer>
        <div class="footer-content">
            <div class="social-links">
                <a href="https://x.com/waspross"><i class="fab fa-twitter"></i></a>
                <a href="https://instagram.com/waspros"><i class="fab fa-instagram"></i></a>
                <a href="https://github.com/GitHub"><i class="fab fa-github"></i></a>
                <a href="https://t.me/waspros"><i class="fab fa-telegram"></i></a>
            </div>
            <p class="copyright">© {{ current_year }} Areszyn Music Downloader. All rights reserved.</p>
        </div>
    </footer>

    <script>
        // Show loading spinner when form is submitted
        document.getElementById('download-form').addEventListener('submit', function() {
            document.getElementById('loading-spinner').style.display = 'block';
        });

        // Auto-focus the URL input when page loads
        window.onload = function() {
            document.getElementById('url').focus();
        };
    </script>
</body>
</html>
"""

def seconds_to_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_file_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def clean_filename(filename):
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    return filename[:100]

def search_lyrics(title, artist):
    try:
        # You could integrate with a lyrics API here
        # For now, we'll return a placeholder
        return f"Lyrics for {title} by {artist} could not be automatically retrieved.\n\nTry searching on Genius or other lyrics websites."
    except Exception as e:
        logger.error(f"Lyrics search error: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    current_year = datetime.now().year

    if request.method == "POST":
        url = request.form.get("url")
        if not url or "youtube.com" not in url and "youtu.be" not in url:
            return render_template_string(HTML,
                                       error="Please enter a valid YouTube URL",
                                       preview=False,
                                       current_year=current_year)

        try:
            # Get user preferences
            audio_format = request.form.get("format", "mp3")
            add_metadata = request.form.get("add_metadata", "on") == "on"
            add_lyrics = request.form.get("add_lyrics", "off") == "on"

            # Generate unique ID for filename
            unique_id = str(uuid.uuid4())
            outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s")

            # Configure yt-dlp options based on user preferences
            ydl_opts = {
                "outtmpl": outtmpl,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
            }

            # Set format based on user selection
            if audio_format == "mp3":
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }]
                })
            elif audio_format == "mp3_high":
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }]
                })
            elif audio_format == "flac":
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "flac",
                    }]
                })
            elif audio_format == "m4a":
                ydl_opts.update({
                    "format": "bestaudio[ext=m4a]",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "m4a",
                    }]
                })
            elif audio_format == "opus":
                ydl_opts.update({
                    "format": "bestaudio[ext=webm]",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "opus",
                    }]
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Handle playlist items
                playlist = None
                if "_type" in info and info["_type"] == "playlist":
                    playlist = {
                        "title": info.get("title", "Unknown Playlist"),
                        "count": len(info.get("entries", []))
                    }
                    # Use the first video in the playlist
                    info = info["entries"][0]

            # Determine the downloaded file extension
            ext = "mp3"
            if audio_format == "flac":
                ext = "flac"
            elif audio_format == "m4a":
                ext = "m4a"
            elif audio_format == "opus":
                ext = "opus"

            audio_file = os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.{ext}")
            if not os.path.exists(audio_file):
                return render_template_string(HTML,
                                           error="Failed to download audio.",
                                           preview=False,
                                           current_year=current_year)

            # Get file size
            file_size = format_file_size(os.path.getsize(audio_file))

            # Extract metadata
            title = info.get("title", "Unknown Title")
            artist = info.get("uploader", "Unknown Artist")
            duration = seconds_to_time(info.get("duration", 0))
            thumbnail = info.get("thumbnail", "https://envs.sh/YTD.jpg")

            # Get quality info
            quality = "Standard"
            if audio_format == "mp3_high":
                quality = "High (320kbps)"
            elif audio_format == "flac":
                quality = "Lossless (FLAC)"
            elif audio_format == "m4a":
                quality = "AAC (M4A)"
            elif audio_format == "opus":
                quality = "Opus"

            # Clean filename for download
            clean_title = clean_filename(title)
            filename = f"{clean_title}.{ext}"

            # Embed metadata if requested
            if add_metadata and ext in ["mp3", "flac"]:
                try:
                    if ext == "mp3":
                        audio = MP3(audio_file, ID3=ID3)
                    else:  # FLAC
                        audio = FLAC(audio_file)

                    try:
                        audio.add_tags()
                    except error:
                        pass

                    audio.tags.add(TIT2(encoding=3, text=title))
                    audio.tags.add(TPE1(encoding=3, text=artist))

                    # Try to get album info
                    album = info.get("album", "")
                    if album:
                        audio.tags.add(TALB(encoding=3, text=album))

                    # Download and embed thumbnail
                    img_data = requests.get(thumbnail).content
                    if ext == "mp3":
                        audio.tags.add(
                            APIC(
                                encoding=3,
                                mime='image/jpeg',
                                type=3,
                                desc='Cover',
                                data=img_data
                            )
                        )
                    else:  # FLAC
                        pic = Picture()
                        pic.data = img_data
                        pic.type = 3  # Front cover
                        pic.mime = 'image/jpeg'
                        audio.add_picture(pic)

                    audio.save()
                except Exception as e:
                    logger.error(f"Metadata embedding error: {e}")

            # Search for lyrics if requested
            lyrics = None
            if add_lyrics:
                lyrics = search_lyrics(title, artist)

            return render_template_string(HTML,
                preview=True,
                title=title,
                artist=artist,
                duration=duration,
                thumbnail=thumbnail,
                audio_url=url_for("download_file", filename=f"{unique_id}.{ext}"),
                filename=filename,
                quality=quality,
                size=file_size,
                lyrics=lyrics,
                playlist=playlist,
                error=None,
                current_year=current_year
            )

        except Exception as e:
            logger.error(f"Download error: {e}")
            return render_template_string(HTML,
                                       error="Failed to process your request. Please try a different video or check the URL.",
                                       preview=False,
                                       current_year=current_year)

    return render_template_string(HTML, preview=False, current_year=current_year)

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        # Clean up the file after sending (optional)
        try:
            response = send_file(filepath, as_attachment=True)

            # Schedule file cleanup after 1 hour
            # You might want to implement a proper cleanup job in production
            # import threading
            # timer = threading.Timer(3600, os.remove, args=[filepath])
            # timer.start()

            return response
        except Exception as e:
            logger.error(f"File download error: {e}")
            return "Error serving file", 500
    return "File not found", 404

@app.route("/api/info", methods=["GET"])
def get_video_info():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "simulate": True,
            "extract_flat": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            response = {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
                "formats": []
            }

            # Add available formats
            if "formats" in info:
                for fmt in info["formats"]:
                    if fmt.get("audio_ext") != "none":
                        response["formats"].append({
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "acodec": fmt.get("acodec"),
                            "abr": fmt.get("abr"),
                            "asr": fmt.get("asr"),
                            "filesize": fmt.get("filesize"),
                        })

            return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
