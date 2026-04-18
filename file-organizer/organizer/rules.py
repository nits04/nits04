DEFAULT_TYPE_RULES = {
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
        ".webp", ".ico", ".tiff", ".tif", ".heic", ".raw",
    ],
    "Videos": [
        ".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv",
        ".webm", ".m4v", ".3gp", ".mpeg", ".mpg",
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
        ".m4a", ".opus", ".aiff",
    ],
    "Documents": [
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
        ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".odp",
        ".csv", ".epub", ".md",
    ],
    "Archives": [
        ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
        ".xz", ".lz", ".lzma", ".cab", ".iso",
    ],
    "Code": [
        ".py", ".js", ".ts", ".html", ".css", ".java",
        ".cpp", ".c", ".h", ".cs", ".go", ".rs", ".rb",
        ".php", ".swift", ".kt", ".sh", ".bash", ".json",
        ".xml", ".yaml", ".yml", ".toml", ".sql", ".r",
    ],
    "Executables": [
        ".exe", ".msi", ".dmg", ".app", ".deb", ".rpm",
        ".bin", ".run", ".apk",
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ],
    "Ebooks": [
        ".epub", ".mobi", ".azw", ".azw3",
    ],
    "Torrents": [
        ".torrent",
    ],
}

IGNORED_FILES = {
    ".ds_store", "thumbs.db", "desktop.ini", ".localized",
    ".gitignore", ".gitkeep",
}


def build_extension_map(rules: dict) -> dict:
    ext_map = {}
    for folder, extensions in rules.items():
        for ext in extensions:
            ext_map[ext.lower()] = folder
    return ext_map
