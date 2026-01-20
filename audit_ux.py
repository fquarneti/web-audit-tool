import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
from PIL import Image
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# CONFIGURAZIONE
API_KEY = "AIzaSyBUMACiDRdQ_6vvFPR6AIazRjUD68E2bok"
genai.configure(api_key=API_KEY)
MODEL_NAME = 'models/gemini-3-flash-preview'

async def run_full_audit(url):
    async with async_playwright() as p:
        print(f"🌐 Avvio Audit Completo su: {url}")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # --- PILASTRO 1 & 3: ESTRAZIONE DATI TECNICI E SEO ---
            seo_data = await page.evaluate("""() => {
                const getTags = (selector) => Array.from(document.querySelectorAll(selector)).map(el => el.innerText.trim());
                return {
                    title: document.title,
                    description: document.querySelector('meta[name="description"]')?.content || 'Mancante',
                    h1: getTags('h1'),
                    h2: getTags('h2'),
                    scripts: Array.from(document.querySelectorAll('script')).map(s => s.src).filter(src => src !== '')
                };
            }""")

            # --- PILASTRO 4: UX (SCREENSHOT) ---
            screenshot_path = "audit_screenshot.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            
            img = Image.open(screenshot_path)
            model = genai.GenerativeModel(MODEL_NAME)

            # --- IL SUPER PROMPT (Unisce i pilastri) ---
            prompt = f"""
            Agisci come un consulente Web Agency Senior. Analizza il sito basandoti su questi dati e sull'immagine allegata.
            
            DATI SEO E TECNICI:
            - Titolo: {seo_data['title']}
            - Meta Description: {seo_data['description']}
            - Tag H1: {seo_data['h1']}
            - Tag H2: {seo_data['h2'][:5]} (primi 5)
            
            TRACKING:
            - Script trovati: {seo_data['scripts'][:10]}
            
            COMPITI:
            1. SEO: I tag H1 e il Titolo sono ottimizzati?
            2. UX/UI: Guarda lo screenshot. Il design è moderno e la CTA è chiara?
            3. TECNICO: Identifica se ci sono script di tracking (GA4, FB Pixel) o se è un sito WordPress.
            4. PRIORITÀ: Dimmi la prima cosa da cambiare per vendere di più.
            
            Rispondi in italiano con un formato professionale (usa il grassetto per i punti chiave).
            """

            print("🧠 L'IA sta incrociando i dati tecnici con l'analisi visiva...")
            response = model.generate_content([prompt, img])
            
            print("\n" + "═"*50)
            print("🚀 REPORT FINALE MULTI-PILASTRO")
            print("═"*50)
            print(response.text)
            print("═"*50)

        except Exception as e:
            print(f"❌ Errore: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_full_audit("https://www.apple.com/it/"))