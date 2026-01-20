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

# --- LOGICA DI AUDIT TECNICO E VISIVO ---
async def run_audit(url, api_key):
    genai.configure(api_key=api_key)
    
    # Impostazioni di sicurezza per evitare rifiuti dell'IA (Finish Reason 1)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    screenshot_path = "/tmp/screenshot.png"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            # 1. Navigazione e acquisizione dati tecnici
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Estrazione CMS, Plugin e Librerie via JavaScript
            tech_data = await page.evaluate("""() => {
                const scripts = Array.from(document.querySelectorAll('script')).map(s => s.src.toLowerCase());
                const html = document.documentElement.innerHTML.toLowerCase();
                
                // Rilevamento CMS
                const isWP = html.includes('wp-content') || html.includes('wp-includes');
                
                // Rilevamento Plugin (estratto dai percorsi wp-content)
                const plugins = scripts.filter(s => s.includes('wp-content/plugins/'))
                                       .map(s => s.split('plugins/')[1].split('/')[0]);
                
                return {
                    cms: isWP ? "WordPress" : "Altro/Non rilevato",
                    meta_generator: document.querySelector('meta[name="generator"]')?.content || "N/A",
                    plugins: [...new Set(plugins)],
                    libraries: {
                        jquery: scripts.some(s => s.includes('jquery')),
                        react: scripts.some(s => s.includes('react')),
                        bootstrap: scripts.some(s => s.includes('bootstrap')),
                        tracking_google: scripts.some(s => s.includes('gtag') || s.includes('analytics')),
                        tracking_pixel: scripts.some(s => s.includes('fbevents'))
                    }
                };
            }""")
            
            # 2. Screenshot per analisi visiva
            await page.screenshot(path=screenshot_path)
            img = Image.open(screenshot_path)
            
            # 3. Prompt multimodale (Codice + Immagine)
            prompt = f"""
            Analizza questo sito web basandoti sullo screenshot e su questi dati tecnici:
            - CMS: {tech_data['cms']}
            - Plugin rilevati: {tech_data['plugins'][:8]}
            - Librerie/Tracking: {tech_data['libraries']}
            
            Fornisci un report professionale in italiano:
            1. Analisi Tecnica: Commenta la tecnologia rilevata (es. WordPress, plugin attivi, tracciamenti mancanti).
            2. Analisi UX/UI: Commenta l'impatto visivo e la chiarezza dell'interfaccia.
            3. Consiglio Strategico: Dimmi la prima cosa tecnica o estetica da cambiare per migliorare il sito.
            """
            
            response = model.generate_content([prompt, img], safety_settings=safety_settings)
            
            # Controllo validità risposta
            if response.candidates and response.candidates[0].content.parts:
                return response.text, screenshot_path, tech_data
            else:
                return "L'IA ha bloccato l'analisi visiva. Ecco i dati tecnici grezzi.", screenshot_path, tech_data
                
        finally:
            await browser.close()

# --- INTERFACCIA UTENTE (STREAMLIT) ---
st.title("🔍 AI Web Auditor Professional")
st.markdown("Analisi multimodale: Visiva (Gemini 3) + Tecnica (Playwright Scraper)")

# Configurazione API Key dai Secrets o Sidebar
api_key = st.secrets.get("GEMINI_KEY", st.sidebar.text_input("Gemini API Key", type="password"))

target_url = st.text_input("Inserisci l'URL da analizzare:", placeholder="https://www.esempio.it")

if st.button("🚀 Avvia Audit Completo"):
    if not target_url or not api_key:
        st.warning("Inserisci URL e API Key per continuare.")
    else:
        try:
            with st.spinner("Scansione tecnica e interrogazione Gemini 3 in corso..."):
                report, ss_path, tech_info = asyncio.run(run_audit(target_url, api_key))
                
                st.success("✅ Analisi completata!")
                
                # Layout a Tab per pulizia visiva
                tab_report, tab_tech = st.tabs(["📄 Report Strategico", "🛠️ Stack Tecnologico"])
                
                with tab_report:
                    col_img, col_txt = st.columns([1, 1])
                    with col_img:
                        st.image(ss_path, caption="Screenshot Analizzato", use_container_width=True)
                    with col_txt:
                        st.markdown(report)
                
                with tab_tech:
                    st.subheader("Dettagli Tecnici Rilevati")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("CMS", tech_info['cms'])
                    c2.metric("Meta Generator", tech_info['meta_generator'][:20])
                    lib_count = sum(1 for v in tech_info['libraries'].values() if v)
                    c3.metric("Tracking/Lib JS", f"{lib_count} rilevate")
                    
                    st.divider()
                    
                    col_p, col_l = st.columns(2)
                    with col_p:
                        st.write("**Plugin WordPress:**")
                        if tech_info['plugins']:
                            st.json(tech_info['plugins'])
                        else:
                            st.write("Nessun plugin WP identificato (o sito non WordPress).")
                    
                    with col_l:
                        st.write("**Tracking & Librerie:**")
                        st.write(tech_info['libraries'])

        except Exception as e:
            st.error(f"Errore durante l'audit: {e}")

st.divider()
st.caption("AI Web Auditor v3.0 • Tecnologia 2026")