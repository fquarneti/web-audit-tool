import streamlit as st
import os
import subprocess

# --- TRUCCO PER STREAMLIT CLOUD 2026 ---
# Questo script viene eseguito all'avvio per assicurarsi che i browser esistano
if "playwright_installed" not in st.session_state:
    try:
        # Installa i browser necessari
        subprocess.run(["playwright", "install", "chromium"])
        st.session_state["playwright_installed"] = True
    except Exception as e:
        st.error(f"Errore installazione browser: {e}")

import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Web Auditor 🚀", layout="wide")

# --- FUNZIONE INSTALLAZIONE BROWSER ---
# Necessaria per Streamlit Cloud
def install_playwright():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Errore durante l'installazione dei browser: {e}")

# --- LOGICA DI AUDIT ---
async def run_audit(url, api_key):
    # Configurazione AI
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    
    # Cartella temporanea sicura per Linux/Streamlit Cloud
    screenshot_path = "/tmp/screenshot.png"
    
    async with async_playwright() as p:
        # Lancio browser con argomenti di sicurezza per il cloud
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Estrazione dati tecnici (Pilastro SEO/Tecnico)
            title = await page.title()
            h1 = await page.evaluate("() => Array.from(document.querySelectorAll('h1')).map(el => el.innerText)")
            
            # Screenshot
            await page.screenshot(path=screenshot_path)
            
            # Analisi Multimodale
            img = Image.open(screenshot_path)
            prompt = f"""
            Agisci come un esperto Senior di UX e SEO. 
            Dati tecnici estratti:
            - Titolo: {title}
            - Tag H1: {h1}
            
            Analizza lo screenshot e i dati sopra per fornire un report in italiano suddiviso in:
            1. Valutazione Visiva (UX/UI)
            2. Ottimizzazione SEO (Titoli e Struttura)
            3. Consiglio d'oro per aumentare le conversioni.
            """
            
            response = model.generate_content([prompt, img])
            return response.text, screenshot_path
            
        finally:
            await browser.close()

# --- INTERFACCIA UTENTE (UI) ---
st.title("🚀 AI Web Auditor Professional")
st.sidebar.header("Configurazione")
user_api_key = st.sidebar.text_input("Gemini API Key", value="AIzaSyBUMACiDRdQ_6vvFPR6AIazRjUD68E2bok", type="password")

target_url = st.text_input("Inserisci l'URL del sito da analizzare:", placeholder="https://www.esempio.it")

if st.button("Avvia Audit Completo"):
    if not target_url or not user_api_key:
        st.warning("Inserisci sia l'URL che la API Key.")
    else:
        # Assicuriamoci che i browser siano pronti (solo per il cloud)
        if not os.path.exists("/home/adminuser/.cache/ms-playwright"):
            with st.spinner("Installazione browser in corso (solo primo avvio)..."):
                install_playwright()
        
        try:
            with st.spinner("Analisi in corso... Gemini sta osservando il sito..."):
                # Eseguiamo la funzione asincrona
                report_text, ss_path = asyncio.run(run_audit(target_url, user_api_key))
                
                st.success("✅ Audit Completato!")
                
                # Visualizzazione Risultati
                col_img, col_txt = st.columns([1, 1])
                
                with col_img:
                    st.subheader("📸 Screenshot")
                    if os.path.exists(ss_path):
                        st.image(ss_path, use_container_width=True)
                
                with col_txt:
                    st.subheader("🧠 Analisi IA")
                    st.markdown(report_text)
                    
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")

st.divider()
st.caption("Creato con Gemini 3 & Streamlit • 2026 Edition")