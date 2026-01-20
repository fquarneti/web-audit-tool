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

# --- LOGICA DI AUDIT AVANZATA (WAPPALYZER STYLE) ---
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
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # --- ANALISI TECNICA ESTESA (IL "PEZZO LUNGO") ---
            tech_data = await page.evaluate("""() => {
                const html = document.documentElement.innerHTML;
                const scripts = Array.from(document.querySelectorAll('script')).map(s => s.src || '');
                const links = Array.from(document.querySelectorAll('link')).map(l => l.href || '');
                
                const exists = (sel) => document.querySelector(sel) !== null;
                const checkPath = (pat) => scripts.some(s => s.includes(pat)) || links.some(l => l.includes(pat));

                return {
                    "Piattaforma & CMS": {
                        "WordPress": exists('link[href*="wp-content"]') || checkPath('wp-includes'),
                        "Shopify": window.Shopify || checkPath('cdn.shopify.com'),
                        "Wix": window.wixEmbedsAPI || checkPath('wixstatic.com'),
                        "Squarespace": window.Static && window.Static.SQUARESPACE_CONTEXT,
                        "Magento": exists('script[src*="/static/frontend/"]') || window.Magento,
                        "Joomla": checkPath('com_content'),
                        "PrestaShop": window.prestashop || checkPath('prestashop')
                    },
                    "Page Builders": {
                        "Divi": exists('#et-main-area') || exists('.et_pb_section') || checkPath('themes/Divi'),
                        "Elementor": window.elementorFrontend || exists('.elementor'),
                        "WPBakery": exists('.vc_row') || checkPath('js_composer'),
                        "Oxygen": exists('.ct-section') || checkPath('plugins/oxygen'),
                        "Gutenberg": exists('.wp-block-group') || exists('link[href*="block-library"]'),
                        "Webflow": exists('html[data-wf-page]') || checkPath('webflow.js')
                    },
                    "Marketing & SEO": {
                        "Yoast SEO": html.includes('yoast-schema-graph'),
                        "Rank Math": html.includes('rank-math'),
                        "HubSpot": window._hsq || checkPath('js.hs-scripts.com'),
                        "Mailchimp": checkPath('chimpStatic') || exists('#mc-embedded-subscribe-form')
                    },
                    "Analytics & Tracking": {
                        "GA4": window.google_tag_data || checkPath('gtag/js'),
                        "FB Pixel": window.fbq || checkPath('fbevents.js'),
                        "Hotjar": window.hj || checkPath('hotjar-'),
                        "Clarity": window.clarity || checkPath('clarity.ms')
                    },
                    "Librerie & CSS": {
                        "jQuery": window.jQuery,
                        "React": window.React || exists('[data-reactroot]'),
                        "Vue.js": window.Vue || exists('[data-v-'),
                        "Bootstrap": window.bootstrap || checkPath('bootstrap'),
                        "Tailwind": html.includes('tailwind') || html.includes('tw-'),
                        "FontAwesome": checkPath('font-awesome') || exists('.fa-')
                    }
                };
            }""")
            
            # Screenshot e analisi visiva
            await page.screenshot(path=screenshot_path)
            img = Image.open(screenshot_path).convert("RGB")
            
            prompt = f"""
            Analizza questo sito web.
            STACK TECNICO RILEVATO: {tech_data}
            
            Fornisci un report dettagliato in italiano:
            1. Analisi dello Stack: Quali vantaggi o svantaggi portano queste tecnologie al sito?
            2. Analisi UX: Valuta l'aspetto visivo basandoti sullo screenshot.
            3. Errori e Opportunità: Cosa manca (es. pixel mancanti, builder pesanti)?
            """
            
            try:
                response = model.generate_content([prompt, img], safety_settings=safety_settings)
                report_text = response.text if (response.candidates and response.candidates[0].content.parts) else "L'IA ha bloccato l'analisi visiva (Finish Reason 1). Consulta i dati tecnici sotto."
            except:
                report_text = "Errore durante la generazione del report IA. Consulta i dati tecnici rilevati manualmente."
                
            return report_text, screenshot_path, tech_data
            
        finally:
            await browser.close()

# --- INTERFACCIA STREAMLIT ---
st.title("🚀 AI Web Auditor Pro - Deep Analysis")

api_key = st.secrets.get("GEMINI_KEY", st.sidebar.text_input("Gemini API Key", type="password"))
target_url = st.text_input("Inserisci URL:", placeholder="https://www.esempio.it")

if st.button("Avvia Scansione Profonda"):
    if not target_url or not api_key:
        st.warning("Mancano dati.")
    else:
        try:
            with st.spinner("Eseguendo analisi tecnica stile Wappalyzer..."):
                report, ss_path, tech = asyncio.run(run_audit(target_url, api_key))
                
                st.success("Audit Completato!")
                
                tab1, tab2 = st.tabs(["📝 Report Strategico IA", "🛠️ Analisi Tecnica Dettagliata"])
                
                with tab1:
                    c1, c2 = st.columns([1, 1.2])
                    c1.image(ss_path, caption="Analisi Visiva")
                    c2.markdown(report)
                
                with tab2:
                    st.subheader("Fingerprinting Tecnologico")
                    for cat, items in tech.items():
                        found = [k for k, v in items.items() if v]
                        if found:
                            with st.expander(f"✅ {cat}", expanded=True):
                                cols = st.columns(len(found) if len(found) > 0 else 1)
                                for i, item in enumerate(found):
                                    cols[i % len(found)].info(item)
                        else:
                            st.write(f"⚪ **{cat}**: Nessun elemento rilevato.")

        except Exception as e:
            st.error(f"Errore: {e}")