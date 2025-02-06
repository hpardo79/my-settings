from datetime import date
import json
import os
import subprocess
from pathlib import Path
import requests

FEED_URL = 'https://peapix.com/bing/feed?country='
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
}

def get_wallpapers_feed(country: str):
    """Obtiene el feed de imágenes de Bing en formato JSON."""
    response = requests.get(f"{FEED_URL}{country}", headers=DEFAULT_HEADERS)
    response.raise_for_status()
    return response.json()

def download_image(url: str, path: Path):
    """Descarga una imagen si no existe en el directorio."""
    if path.exists():
        return
    response = requests.get(url, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    path.write_bytes(response.content)

def get_connected_monitors():
    """Obtiene los nombres de los monitores conectados."""
    result = subprocess.run(['xrandr'], capture_output=True, text=True)
    return [line.split()[0] for line in result.stdout.splitlines() if " connected" in line]

def set_wallpaper(image_path: Path):
    """Configura el fondo de pantalla en XFCE para todos los monitores."""
    monitors = get_connected_monitors()
    commands = [
        ['xfconf-query', '-c', 'xfce4-desktop', '-p', f'/backdrop/screen0/monitor{monitor}/workspace0/last-image', '-s', str(image_path)]
        for monitor in monitors
    ]
    for cmd in commands:
        subprocess.run(cmd)

def main():
    """Función principal."""
    if not os.environ.get('DISPLAY'):
        print('$DISPLAY not set')
        return

    country = os.environ.get('BING_WALLPAPER_COUNTRY', '')
    wallpapers_dir = Path(os.environ.get('BING_WALLPAPER_PATH', Path.home() / '.wallpapers'))
    wallpapers_dir.mkdir(parents=True, exist_ok=True)

    # Descarga el feed y las imágenes
    feed = get_wallpapers_feed(country)
    for item in feed:
        image_path = wallpapers_dir / f"{item['date']}.jpg"
        download_image(item['imageUrl'], image_path)

    # Configura el fondo de pantalla
    today_wallpaper = wallpapers_dir / f"{date.today().isoformat()}.jpg"
    if today_wallpaper.exists():
        set_wallpaper(today_wallpaper)

if __name__ == '__main__':
    main()
