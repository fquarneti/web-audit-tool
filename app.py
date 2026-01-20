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
    # Nota: Su Gemini 3 queste impostazioni sono fondamentali
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    # UTILIZZO DI GEMINI 3 FLASH PREVIEW
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    screenshot_path = "/tmp/screenshot.png"
    
    async with async_playwright() as p:
        # Lancio browser ottimizzato per Cloud
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            # Navigazione
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Screenshot
            await page.screenshot(path=screenshot_path)
            
            # Estrazione Dati Tecnici minimi per il prompt
            title = await page.title()
            
            # Preparazione immagine per l'analisi
            img = Image.open(screenshot_path)
            
            # Prompt tecnico e neutro (per minimizzare i rifiuti dell'IA)
            prompt = f"""
            Esegui un'ispezione tecnica dell'interfaccia utente basata sugli elementi presenti nello screenshot.
            Sito: {title}
            
            1. Descrivi la disposizione degli elementi (layout).
            2. Valuta la chiarezza della gerarchia visiva.
            3. Fornisci 3 suggerimenti tecnici per migliorare l'esperienza utente.
            
            Rispondi in italiano con tono professionale.
            """
            
            # Interrogazione Gemini 3
            response = model.generate_content(
                [prompt, img],
                safety_settings=safety_settings
            )
            
            # Gestione della risposta per evitare crash se bloccata
            try:
                if response.candidates and response.candidates[0].content.parts:
                    return response.text, screenshot_path
                else:
                    # Se non ci sono parti nella risposta, cerchiamo di capire il motivo
                    reason = response.candidates[0].finish_reason if response.candidates else "Sconosciuto"
                    return f"L'analisi è stata bloccata dai filtri di sicurezza (Codice: {reason}). Prova un sito più semplice come example.com.", screenshot_path
            except (ValueError, AttributeError):
                return "Errore nella generazione della risposta. Verifica la tua API Key.", screenshot_path
            
        finally:
            await browser.close()

# --- INTERFACCIA UTENTE (UI) ---
st.title("🔍 AI Web Auditor Professional (Gemini 3)")

# Gestione API KEY dai Segreti o da Sidebar
if "GEMINI_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_KEY"]
else:
    api_key = st.sidebar.text_input("Inserisci Gemini API Key", type="password")

target_url = st.text_input("URL del sito da analizzare:", placeholder="https://www.tuosito.it")

if st.button("🚀 Avvia Analisi Gemini 3"):
    if not target_url or not api_key:
        st.warning("Inserisci URL e API Key.")
    else:
        try:
            with st.spinner("Analisi in corso con Gemini 3... Attendere circa 30 secondi."):
                report, ss_path = asyncio.run(run_audit(target_url, api_key))
                
                st.success("Analisi completata!")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("📸 Screenshot")
                    if os.path.exists(ss_path):
                        st.image(ss_path, use_container_width=True)
                
                with col2:
                    st.subheader("📝 Report Strategico")
                    st.markdown(report)
                    
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")

st.divider()
st.caption("AI Web Auditor v2.2 • Powered by Gemini 3 Flash Preview")