import streamlit as st
import asyncio
import os
import subprocess
from playwright.async_api import async_playwright
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Web Auditor Pro 🚀", layout="wide")

# --- TRUCCO PER STREAMLIT CLOUD ---
if "playwright_installed" not in st.session_state:
    try:
        subprocess.run(["playwright", "install", "chromium"])
        st.session_state["playwright_installed"] = True
    except Exception as e:
        st.error(f"Errore installazione browser: {e}")

# --- LOGICA DI AUDIT AVANZATA (STILE WAPPALYZER) ---
async def run_audit(url, api_key):
    genai.configure(api_key=api_key)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    screenshot_path = "/tmp/screenshot.png"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # --- ANALISI TECNICA AVANZATA ---
            tech_data = await page.evaluate("""() => {
                const html = document.documentElement.innerHTML;
                const scripts = Array.from(document.querySelectorAll('script')).map(s => s.src || '');
                const links = Array.from(document.querySelectorAll('link')).map(l => l.href || '');
                
                const detect = (pattern) => html.includes(pattern) || scripts.some(s => s.includes(pattern)) || links.some(l => l.includes(pattern));

                return {
                    cms: {
                        wordpress: detect('wp-content'),
                        shopify: detect('cdn.shopify.com') || window.Shopify,
                        joomla: detect('com_content'),
                        wix: detect('wix.com'),
                        magento: detect('mage/') || window.Magento
                    },
                    builders: {
                        elementor: detect('elementor'),
                        divi: detect('et-pb-'),
                        wp_bakery: detect('js_composer'),
                        webflow: detect('wf-')
                    },
                    ecommerce: {
                        woocommerce: detect('woocommerce'),
                        presta: detect('prestashop')
                    },
                    analytics: {
                        ga4: detect('gtag') || detect('google-analytics'),
                        fb_pixel: detect('fbevents.js'),
                        hotjar: detect('hotjar'),
                        clarity: detect('clarity.ms')
                    },
                    ui_frameworks: {
                        bootstrap: detect('bootstrap'),
                        tailwind: html.includes('tailwind'),
                        fontawesome: detect('font-awesome')
                    }
                };
            }""")
            
            await page.screenshot(path=screenshot_path)
            img = Image.open(screenshot_path)
            
            prompt = f"""
            Analizza lo screenshot e questi dati tecnici 'under-the-hood':
            CMS & Piattaforma: {tech_data['cms']}
            Page Builder: {tech_data['builders']}
            E-commerce: {tech_data['ecommerce']}
            Tracking & Analitica: {tech_data['analytics']}
            Framework UI: {tech_data['ui_frameworks']}

            Fornisci un audit professionale:
            1. Analisi Stack Tecnologico: Valuta se la scelta tecnologica è coerente con il tipo di sito.
            2. Analisi UX/UI: Come l'utente interagisce con il layout.
            3. Opportunità: Suggerisci 2 tool o miglioramenti tecnici (es. "Manca Hotjar per registrare le sessioni" o "Passa da Elementor a Gutenberg per velocità").
            """
            
            response = model.generate_content([prompt, img], safety_settings=safety_settings)
            return response.text, screenshot_path, tech_data
            
        finally:
            await browser.close()

# --- INTERFACCIA STREAMLIT ---
st.title("🚀 AI Web Auditor Pro (Wappalyzer Style)")
api_key = st.secrets.get("GEMINI_KEY", st.sidebar.text_input("Gemini API Key", type="password"))
target_url = st.text_input("URL del sito:", placeholder="https://example.com")

if st.button("Avvia Deep Audit"):
    if not target_url or not api_key:
        st.warning("Dati mancanti.")
    else:
        try:
            with st.spinner("Scansione impronte digitali e analisi Gemini 3..."):
                report, ss_path, tech = asyncio.run(run_audit(target_url, api_key))
                
                st.success("Analisi completata!")
                t1, t2 = st.tabs(["📝 Report IA", "🔍 Tech Stack Detagliato"])
                
                with t1:
                    c1, c2 = st.columns([1, 1.2])
                    c1.image(ss_path, use_container_width=True)
                    c2.markdown(report)
                
                with t2:
                    st.subheader("Tecnologie Identificate")
                    # Creiamo delle card per le tecnologie trovate
                    cols = st.columns(4)
                    
                    # Logica per mostrare solo ciò che è stato trovato
                    categories = {
                        "CMS": tech['cms'],
                        "Builders": tech['builders'],
                        "E-com": tech['ecommerce'],
                        "Analytics": tech['analytics']
                    }
                    
                    for i, (name, data) in enumerate(categories.items()):
                        found = [k.capitalize() for k, v in data.items() if v]
                        cols[i % 4].write(f"**{name}**")
                        if found:
                            for item in found: cols[i % 4].success(item)
                        else:
                            cols[i % 4].info("Nessuno")

        except Exception as e:
            st.error(f"Errore: {e}")