"""Script para capturar screenshots reales de la app Streamlit."""
import subprocess
import sys
import time
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    proof_dir = os.path.dirname(script_dir)
    app_dir = os.path.join(proof_dir, "App_streamlit")
    docs_dir = os.path.join(proof_dir, "docs", "images")

    # Iniciar Streamlit en background
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app_steam.py", "--server.headless", "true", "--server.port", "8501"],
        cwd=app_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        time.sleep(20)  # Esperar a que cargue (API puede tardar)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Instala playwright: pip install playwright && playwright install chromium")
            return 1

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto("http://localhost:8501", wait_until="domcontentloaded", timeout=90000)
            time.sleep(5)

            # Tendencias (tab por defecto)
            page.screenshot(path=os.path.join(docs_dir, "tendencias.png"), full_page=True)

            # Clic en Noticias (Streamlit tabs)
            try:
                page.get_by_text("Noticias", exact=True).first.click(timeout=5000)
                time.sleep(4)
                page.screenshot(path=os.path.join(docs_dir, "noticias.png"), full_page=True)
            except Exception:
                pass

            # Clic en Perfil de Jugador
            try:
                page.get_by_text("Perfil de Jugador", exact=True).first.click(timeout=5000)
                time.sleep(3)
                page.screenshot(path=os.path.join(docs_dir, "jugador.png"), full_page=True)
            except Exception:
                pass

            browser.close()

        print("Capturas guardadas en docs/images/")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    return 0

if __name__ == "__main__":
    sys.exit(main())
