import logging
import os
import sys
import requests
import subprocess
from datetime import date
from pathlib import Path
import textwrap
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

# Configuración
FEED_URL = 'https://peapix.com/bing/feed?country='
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
}

def get_feed(country: str) -> list:
    """Obtiene el feed de imágenes de Peapix"""
    url = f"{FEED_URL}{country}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_text_from_url(url: str) -> str:
    """Obtiene el texto de una URL parseando tags h1, h3."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        subtitle = soup.find("h3").get_text(strip=True) if soup.find("h3") else ""
                
        full_text = f"{title}\n{subtitle}"
        return "\n".join(line for line in full_text.splitlines() if line.strip())
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red al obtener texto de {url}: {e}")
    except Exception as e:
        logging.error(f"Error inesperado al obtener texto de {url}: {e}")
    return ""

def download_wallpaper(item: dict, wallpapers_dir: Path) -> Path:
    """Descarga la imagen si no existe aún y le añade el texto de la página."""
    date_str = item.get("date", date.today().isoformat())
    image_url = item.get("imageUrl")
    page_url = item.get("pageUrl")
    
    if not image_url:
        raise ValueError("Campo 'imageUrl' no encontrado en el item del feed")

    image_path = wallpapers_dir / f"{date_str}.jpg"
    if not image_path.exists():
        response = requests.get(image_url, headers=HEADERS)
        response.raise_for_status()
        with open(image_path, "wb") as f:
            f.write(response.content)
        
        if page_url:
            text = get_text_from_url(page_url)
            if text:
                add_text_to_image(image_path, text)
            
    return image_path

def get_connected_monitors() -> list:
    """Detecta monitores conectados vía xrandr"""
    result = subprocess.run(
        ["xrandr"], capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    return [line.split()[0] for line in lines if " connected" in line]

def get_desktop_environment() -> str:
    """Detecta el entorno de escritorio actual."""
    return os.environ.get("XDG_CURRENT_DESKTOP", "unknown").lower()

def set_wallpaper(image_path: Path, desktop_env: str) -> None:
    """Actualiza el fondo de pantalla si el entorno es XFCE."""
    if desktop_env == "xfce":
        monitors = get_connected_monitors()
        for monitor in monitors:
            prop_last_image = f"/backdrop/screen0/monitor{monitor}/workspace0/last-image"
            prop_image_path = f"/backdrop/screen0/monitor{monitor}/workspace0/image-path"
            subprocess.run([
                "xfconf-query", "-c", "xfce4-desktop",
                "-p", prop_last_image, "-s", str(image_path),
                "--create", "-t", "string"
            ])
            subprocess.run([
                "xfconf-query", "-c", "xfce4-desktop",
                "-p", prop_image_path, "-s", str(image_path),
                "--create", "-t", "string"
            ])
    else:
        logging.warning(f"Entorno de escritorio '{desktop_env}' no es XFCE. No se realizarán cambios.")

def add_text_to_image(image_path: Path, text: str):
    """Añade texto (con ajuste de línea) a una imagen."""
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img, "RGBA")
        width, height = img.size

        # Configuración de la fuente
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", size=int(height / 60))
        except IOError:
            font = ImageFont.load_default()

        # Ajuste de línea y padding
        horizontal_padding = int(width / 20)
        vertical_padding = horizontal_padding // 2
        wrap_width = int(width / (font.size * 0.6))
        wrapped_text = textwrap.fill(text, width=wrap_width)

        # Posición del texto
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Ubicación en la parte inferior izquierda con padding
        x = horizontal_padding
        y = height - text_height - vertical_padding

        # Dibujar fondo semitransparente
        bg_x0 = x - 5
        bg_y0 = y - 5
        bg_x1 = x + text_width + 5
        bg_y1 = y + text_height + 5
        draw.rectangle([bg_x0, bg_y0, bg_x1, bg_y1], fill=(0, 0, 0, 112))

        # Dibujar el texto
        draw.text((x, y), wrapped_text, font=font, fill=(255, 255, 255, 255))

        img.save(image_path)
        logging.info(f"Texto añadido a {image_path}")

    except Exception as e:
        logging.error(f"Error al añadir texto a la imagen: {e}")


def main():
    if not os.environ.get("DISPLAY"):
        logging.error("DISPLAY no está definido. ¿Estás en modo gráfico?")
        sys.exit(1)

    # Variables desde entorno o valores por defecto
    country = os.environ.get("BING_WALLPAPER_COUNTRY", "")
    wallpapers_dir = Path(os.environ.get("BING_WALLPAPER_PATH", str(Path.home() / ".wallpapers")))
    wallpapers_dir.mkdir(parents=True, exist_ok=True)

    # Configuración de logging
    log_file = wallpapers_dir / "wallBing.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    try:
        images = get_feed(country)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red al obtener el feed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error inesperado al obtener el feed: {e}")
        sys.exit(1)

    today_str = date.today().isoformat()
    today_image_path = wallpapers_dir / f"{today_str}.jpg"

    for item in images:
        try:
            image_path = download_wallpaper(item, wallpapers_dir)
            if image_path == today_image_path:
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de red descargando imagen: {e}")
        except Exception as e:
            logging.error(f"Error inesperado descargando imagen: {e}")

    if not today_image_path.exists():
        logging.warning(f"No se encontró wallpaper para hoy: {today_str}")
        sys.exit(1)

    try:
        desktop_env = get_desktop_environment()
        set_wallpaper(today_image_path, desktop_env)
        logging.info(f"Wallpaper actualizado para {today_str}")
    except Exception as e:
        logging.error(f"Error al configurar el fondo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
