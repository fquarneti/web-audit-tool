import streamlit as st
import asyncio
import os
import subprocess
from playwright.async_api import async_playwright
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Web Auditor 🚀", layout="wide")

# --- TRUCCO PER STREAMLIT CLOUD (BROWSER INSTALL) ---
if "playwright_installed" not in st.session_state:
    try:
        subprocess.run(["playwright", "install", "chromium"])
        st.session_state["playwright_installed"] = True
    except Exception as e:
        st.error(f"Errore installazione browser: {e}")

# --- LOGICA DI AUDIT ASINCRONA ---
async def run_audit(url, api_key):
    # Configurazione AI
    genai.configure(api_key=api_key)
    
    # Impostazioni di sicurezza per evitare blocchi (Finish Reason 1)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    screenshot_path = "/tmp/screenshot.png"
    
    async with async_playwright() as p:
        # Lancio browser ottimizzato per Cloud
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            # Caricamento Pagina
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Estrazione Dati Tecnici
            title = await page.title()
            h1_tags = await page.evaluate("() => Array.from(document.querySelectorAll('h1')).map(el => el.innerText)")
            h1_text = h1_tags[0] if h1_tags else "Nessun H1 trovato"
            
            # Screenshot
            await page.screenshot(path=screenshot_path)
            
            # Analisi Visiva
            img = Image.open(screenshot_path)
            prompt = f"""
            Analizza questo sito come un Senior UX/UI Designer e Consulente SEO.
            Dati tecnici rilevati:
            - Titolo: {title}
            - Tag H1: {h1_text}
            
            Fornisci un report professionale in italiano diviso in 3 sezioni:
            1. Punti di forza e debolezza dell'interfaccia.
            2. Analisi SEO rapida dei testi estratti.
            3. Una singola azione prioritaria da fare subito per migliorare le conversioni.
            """
            
            response = model.generate_content(
                [prompt, img],
                safety_settings=safety_settings
            )
            
            # Controllo validità risposta (Evita l'errore "Part")
            if response.candidates and response.candidates[0].content.parts:
                return response.text, screenshot_path
            else:
                return "L'analisi è stata bloccata dai filtri di sicurezza. Prova un sito diverso o meno complesso.", screenshot_path
            
        finally:
            await browser.close()

# --- INTERFACCIA UTENTE (UI) ---
st.title("🔍 AI Web Auditor Professional")
st.markdown("Analisi completa in tempo reale basata su **Gemini 3** e **Playwright**.")

# Gestione API KEY dai Segreti o da Sidebar
if "GEMINI_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_KEY"]
else:
    api_key = st.sidebar.text_input("Inserisci Gemini API Key", type="password", help="Ottienila su Google AI Studio")

target_url = st.text_input("URL del sito da analizzare:", placeholder="https://www.tuosito.it")

if st.button("🚀 Avvia Analisi Multimodale"):
    if not target_url or not api_key:
        st.warning("Assicurati di inserire sia l'URL che l'API Key.")
    else:
        try:
            with st.spinner("Catturando il sito e interrogando l'IA... Attendere circa 30 secondi."):
                report, ss_path = asyncio.run(run_audit(target_url, api_key))
                
                st.success("Analisi completata!")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("📸 Screenshot")
                    st.image(ss_path, use_container_width=True)
                
                with col2:
                    st.subheader("📝 Report Strategico")
                    st.markdown(report)
                    
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")
            st.info("💡 Tip: Se vedi errori relativi al browser, prova a fare un 'Reboot App' dalla dashboard di Streamlit.")

st.divider()
st.caption("AI Web Auditor v2.1 • Strumento professionale di analisi tecnica")