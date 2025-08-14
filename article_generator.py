import streamlit as st
import streamlit.components.v1 as components
import os, re, uuid
from datetime import datetime
from string import capwords
import textwrap
import json

# Helper function
def contains_keyword(text, keyword):
    return keyword.lower() in text.lower()

# Generate HTML content
def generate_html(title, meta_desc, slug, content):
    # Usa il blocco WordPress anche nell'anteprima HTML
    wp_block = generate_wp_article_block(title, meta_desc, content)
    return f"""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="https://ti-aiuto.io/{slug}">
</head>
<body>
  {wp_block}
</body>
</html>
"""

def generate_wp_article_block(title, meta_desc, content):
    # Indenta ogni riga del contenuto con 4 spazi
    content_indented = "\n".join("    " + line if line.strip() else "" for line in content.splitlines())
    return f"""
<header class="entry-header">
    <h1 class="entry-title">{title}</h1>
</header>

<div class="ti-aiuto-seobox">
    <strong>Titolo:</strong> {title}<br>
    <strong>Descrizione:</strong> {meta_desc}
</div>

<div class="toc-container">
    [ez-toc]
</div>

<div class="entry-content">
{content_indented}
</div>
"""

# Save HTML file
def create_html_file(title, meta_desc, slug, content):
    slug = slug.strip() or "articolo"
    articoli_dir = os.path.join(os.getcwd(), "output", "articoli")
    os.makedirs(articoli_dir, exist_ok=True)
    filename = os.path.join(articoli_dir, f"{slug}.html")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(generate_html(title, meta_desc, slug, content))
    return filename

# Static list of rules
RANK_MATH_RULES = [
    "La parola chiave di riferimento deve essere nel titolo SEO.",
    "La parola chiave di riferimento deve essere nella metadescrizione SEO.",
    "La parola chiave di riferimento deve essere nell'URL.",
    "La parola chiave di riferimento deve comparire nelle prime 10% parole del contenuto.",
    "La parola chiave di riferimento deve trovarsi nel contenuto.",
    "Il contenuto deve essere più lungo di 600 parole.",
    "La parola chiave deve trovarsi in almeno un sottotitolo (H2, H3...).",
    "La parola chiave principale deve trovarsi nell'alt text delle immagini.",
    "La densità della parola chiave deve essere tra 1% e 1.5%.",
    "L'URL deve contenere massimo 75 caratteri e usare '-' per gli spazi.",
    "Devono essere presenti link a risorse esterne.",
    "Deve essere presente almeno un link DoFollow.",
    "Devono essere presenti link interni.",
    "La parola chiave principale deve essere all'inizio del titolo SEO.",
    "Il titolo deve contenere almeno una parola potente.",
    "Il titolo SEO deve contenere almeno un numero.",
    "Usare paragrafi brevi.",
    "Il contenuto deve contenere immagini e/o video."
]

# Regola custom (non Rank Math)
CUSTOM_RULES = [
    "Il titolo deve essere in Title Case (solo le parole importanti con iniziale maiuscola, le altre minuscole)."
]
def rule_title_titlecase(title, **kwargs):
    stopwords = set([
        # Articoli articolati
        "al", "allo", "alla", "ai", "agli", "alle",
        "dal", "dallo", "dalla", "dai", "dagli", "dalle",
        "nel", "nello", "nella", "nei", "negli", "nelle",
        "sul", "sullo", "sulla", "sui", "sugli", "sulle",
        # Preposizioni semplici
        "a", "ad", "con", "da", "di", "in", "su", "per", "tra", "fra",
        "oltre", "verso", "presso", "durante", "fino", "senza", "sopra",
        "sotto", "oltreché", "attorno", "secondo", "tramite", "compreso",
        "eccetto", "salvo", "tranne",
        # Congiunzioni
        "e", "ed", "ma", "anche", "o", "oppure", "però", "né", "né…né",
        "se", "invece", "anziché", "mentre", "poiché", "perché", "che",
        "affinché", "benchè", "quando", "dove", "come",
        # Avverbi e locuzioni avverbiali
        "non", "mai", "già", "ancora", "appena", "subito", "poi", "quindi",
        "dunque", "perciò", "quasi", "quasi", "proprio", "soltanto", "solo",
        "addirittura", "addirittura", "apparentemente", "addirittura", "addirittura",
        "esattamente", "effettivamente", "generalmente", "normalmente",
        "solitamente", "principalmente", "specificamente", "praticamente",
        "precisamente", "relativamente", "veramente", "ovviamente",
        # Pronomi
        "io", "tu", "lui", "lei", "noi", "voi", "loro",
        "mi", "ti", "si", "ci", "vi", "ne", "lo", "la", "li", "le", "gli",
        # Aggettivi e pronomi dimostrativi/interrogativi
        "questo", "questa", "questi", "queste", "quello", "quella", "quelli", "quelle",
        "un", "uno", "una", "alcun", "alcuno", "alcuna", "alcuni", "alcune",
        "qualcosa", "qualcuno", "qualche", "quale", "quali", "quanto", "quanta",
        "quanti", "quante",
        # Particelle e variazioni
        "ciò", "cui", "chi", "chiunque", "dunque", "ebbene", "insomma", "peraltro",
        "rallegramente", "ribadire", "tuttavia", "ugualmente",
        # Interiezioni/minor words
        "oh", "ah", "beh", "eh", "mah", "ok",
        # Numeri scritti in lettere (se li usi come parole non servono mai in maiuscolo)
        "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci",
        "undici", "dodici", "tredici", "quattordici", "quindici", "sedici",
        "diciassette", "diciotto", "diciannove", "venti", "ventuno", "ventidue",
        # Altri comuni stopwords
        "anche", "ancora", "ancora", "come", "dopo", "durante", "ed", "fra",
        "ido", "laddove", "nulla", "sia", "tale", "tali", "talvolta", "tanto",
        "troppo", "via", "volta", "volte"
    ])

    if not title.strip():
        return False
    words = title.split()
    for i, w in enumerate(words):
        # Salta i token numerici (es. "11")
        if w.isnumeric():
            continue
        if i == 0:
            # Prima parola: se è una stopword di una sola lettera, deve essere MAIUSCOLA
            if w.lower() in stopwords and len(w) == 1:
                if not w.isupper():
                    return False
            else:
                if not (w[:1].isupper() and w[1:].islower()):
                    return False
        else:
            # Parole successive
            if w.lower() in stopwords and len(w) == 1:
                # Stopword di una lettera: deve essere minuscola
                if not w.islower():
                    return False
            elif w.lower() not in stopwords:
                if not (w[:1].isupper() and w[1:].islower()):
                    return False
            else:
                if not w.islower():
                    return False
    return True

def rule_keyword_in_title(title, keyword, **kwargs):
    return contains_keyword(title, keyword)
def rule_keyword_in_meta(meta_desc, keyword, **kwargs):
    return contains_keyword(meta_desc, keyword)
def rule_keyword_in_url(url_slug, keyword, **kwargs):
    # Considera i trattini come spazi quando confronti keyword e slug
    normalized_slug = url_slug.replace('-', ' ')
    return contains_keyword(normalized_slug, keyword)
def rule_keyword_at_start_content(content, keyword, **kwargs):
    # Rimuovi i tag HTML
    content_no_html = re.sub(r'<[^>]+>', '', content)
    # Trova tutte le parole
    words = re.findall(r'\w+', content_no_html)
    if not words:
        return False
    # Calcola il primo 10% delle parole (almeno 1)
    n = max(1, int(len(words) * 0.1))
    first_words = words[:n]
    # Cerca la keyword (case-insensitive) tra le prime parole
    keyword_words = re.findall(r'\w+', keyword.lower())
    first_words_str = ' '.join(first_words).lower()
    return ' '.join(keyword_words) in first_words_str
def rule_keyword_in_content(content, keyword, **kwargs):
    return contains_keyword(content, keyword)
def rule_content_min_words(content, **kwargs):
    # Rimuovi tutti i tag HTML (anche quelli multilinea)
    content_no_html = re.sub(r'<[^>]+>', '', content)
    # Rimuovi anche spazi multipli creati dalla rimozione dei tag
    content_no_html = re.sub(r'\s+', ' ', content_no_html).strip()
    return len(re.findall(r"\w+", content_no_html)) >= 600
def rule_keyword_in_subheading(content, keyword, **kwargs):
    # Cerca la keyword in intestazioni H2/H3 (markdown o HTML)
    # Cerca sia ## che <h2> o <h3>
    pattern = r'(?:##+\s*|<h[23][^>]*>)([^\n<]*)'
    matches = re.findall(pattern, content, re.IGNORECASE)
    return any(contains_keyword(m, keyword) for m in matches)

def rule_keyword_in_img_alt(content, keyword, **kwargs):
    # Cerca la keyword nell'alt delle immagini (markdown o HTML)
    # Markdown: ![alt text](url)
    md_alts = re.findall(r'!\[([^\]]*)\]\([^\)]*\)', content)
    html_alts = re.findall(r'<img [^>]*alt=["\']([^"\']+)["\']', content)
    all_alts = md_alts + html_alts
    return any(contains_keyword(a, keyword) for a in all_alts)

def rule_keyword_density(content, keyword, **kwargs):
    # Densità = occorrenze keyword / numero parole
    words = re.findall(r"\w+", content)
    if not words:
        return False
    count = len(re.findall(re.escape(keyword), content, re.IGNORECASE))
    density = count / len(words)
    return 0.01 <= density <= 0.015  # tra 1% e 1.5%

def rule_url_length_and_dash(url_slug, **kwargs):
    return (
        1 <= len(url_slug) <= 75
        and url_slug == url_slug.lower()
        and (' ' not in url_slug)
        and ('_' not in url_slug)
    )

def rule_external_links(content, **kwargs):
    # Cerca link esterni (markdown o HTML)
    # Markdown: [text](http...)  HTML: <a href="http...">
    md_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
    html_links = re.findall(r'<a [^>]*href=["\']https?://[^"\']+["\']', content)
    return bool(md_links or html_links)

def rule_dofollow_link(content, **kwargs):
    # Trova tutti i link <a ...>
    links = re.findall(r'<a\s+[^>]*>', content, re.IGNORECASE)
    for link in links:
        # Cerca l'attributo rel
        rel_match = re.search(r'rel\s*=\s*["\']([^"\']+)["\']', link, re.IGNORECASE)
        if rel_match:
            rel_value = rel_match.group(1).lower()
            # Se NON contiene nofollow, ugc o sponsored, è dofollow
            if not any(x in rel_value for x in ["nofollow", "ugc", "sponsored"]):
                return True
        else:
            # Se non c'è rel, è dofollow di default
            return True
    return False

def rule_internal_links(content, **kwargs):
    # Cerca link interni (markdown o HTML, senza http/https)
    md_links = re.findall(r'\[([^\]]+)\]\((?!https?://)[^\)]+\)', content)
    html_links = re.findall(r'<a [^>]*href=["\'](?!https?://)[^"\']+["\']', content)
    return bool(md_links or html_links)

def rule_keyword_at_start_title(title, keyword, **kwargs):
    return title.lower().startswith(keyword.lower())

def rule_power_word_in_title(title, **kwargs):
    # Nuova lista di power words fornita dall'utente
    power_words = [
        "incredibile", "sorprendente", "scioccante", "irresistibile", "ufficiale", "garantito", "gratuito", "leader", "veloce", "straordinario", "meraviglioso", "sensazionale", "nuovo", "innovativo", "popolare", "qualità", "efficace", "potente", "esclusivo", "motivante", "sicuro", "unico"
    ]
    # Confronto case-insensitive
    return any(pw.lower() in title.lower() for pw in power_words)

def rule_number_in_title(title, **kwargs):
    return bool(re.search(r'\d', title))

def rule_short_paragraphs(content, **kwargs):
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
    for p in paragraphs:
        p_clean = re.sub(r'<[^>]+>', '', p)
        words = re.findall(r'\w+', p_clean)
        if len(words) > 120:
            return False
    return True

def rule_has_media(content, **kwargs):
    # Cerca immagini o video (markdown o HTML)
    has_img = bool(re.search(r'!\[.*\]\(.*\)|<img ', content))
    has_video = bool(re.search(r'<video |<iframe |\[video\]', content, re.IGNORECASE))
    return has_img or has_video

RULES = [
    {"text": RANK_MATH_RULES[0], "func": rule_keyword_in_title},
    {"text": RANK_MATH_RULES[1], "func": rule_keyword_in_meta},
    {"text": RANK_MATH_RULES[2], "func": rule_keyword_in_url},
    {"text": RANK_MATH_RULES[3], "func": rule_keyword_at_start_content},
    {"text": RANK_MATH_RULES[4], "func": rule_keyword_in_content},
    {"text": RANK_MATH_RULES[5], "func": rule_content_min_words},
    {"text": RANK_MATH_RULES[6], "func": rule_keyword_in_subheading},
    {"text": RANK_MATH_RULES[7], "func": rule_keyword_in_img_alt},
    {"text": RANK_MATH_RULES[8], "func": rule_keyword_density},
    {"text": RANK_MATH_RULES[9], "func": rule_url_length_and_dash},
    {"text": RANK_MATH_RULES[10], "func": rule_external_links},
    {"text": RANK_MATH_RULES[11], "func": rule_dofollow_link},
    {"text": RANK_MATH_RULES[12], "func": rule_internal_links},
    {"text": RANK_MATH_RULES[13], "func": rule_keyword_at_start_title},
    {"text": RANK_MATH_RULES[14], "func": rule_power_word_in_title},
    {"text": RANK_MATH_RULES[15], "func": rule_number_in_title},
    {"text": RANK_MATH_RULES[16], "func": rule_short_paragraphs},
    {"text": RANK_MATH_RULES[17], "func": rule_has_media},
    # Regola custom
    {"text": CUSTOM_RULES[0], "func": rule_title_titlecase, "custom": True},
]

# Funzione che verifica tutte le regole e restituisce lista di tuple (testo, stato)
def check_all_rules(title, meta_desc, url_slug, content, keyword):
    results = []
    for rule in RULES:
        # Passa i parametri richiesti dalla funzione
        status = rule["func"](
            title=title,
            meta_desc=meta_desc,
            url_slug=url_slug,
            content=content,
            keyword=keyword
        )
        results.append({"text": rule["text"], "ok": status})
    return results

# Funzione per mostrare le regole colorate e ordinate
def get_rules_html(title, meta_desc, url_slug, content, keyword):
    # Definisci qui il CSS usato per il rendering delle regole (tooltip, colori, ecc.)
    css = """
    <style>
    .modern-info-wrap {
        position: absolute;
        top: 12px;
        bottom: 12px;
        right: 12px;
        z-index: 2;
        display: flex;
        align-items: center;
        height: auto;
    }
    .modern-info-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 1.5px solid #888;
        color: #555;
        background: #fff;
        font-size: 18px;
        font-weight: 700;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        cursor: pointer;
        transition: border-color 0.2s, color 0.2s;
    }
    .modern-info-icon:hover {
        border-color: #1976d2;
        color: #1976d2;
    }
    .modern-info-wrap:hover .modern-tooltip, .modern-info-wrap:focus-within .modern-tooltip {
        display: block;
    }
    .modern-tooltip {
        display: none;
        position: absolute;
        right: 0;
        top: -70px;
        min-width: 220px;
        max-width: 320px;
        background: #fff;
        color: #222;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.13);
        padding: 14px 18px;
        font-size: 15px;
        font-weight: 400;
        z-index: 1000;
        border: 1px solid #e0e0e0;
    }
    </style>
    """

    results = check_all_rules(title, meta_desc, url_slug, content, keyword)
    # Calcola valori attuali per le regole dove ha senso
    wc = count_words_no_html(content)
    # Densità keyword (conteggio parole SENZA HTML)
    content_no_html = re.sub(r'<[^>]+>', '', content)
    words = re.findall(r"\w+", content_no_html)
    count = len(re.findall(re.escape(keyword), content_no_html, re.IGNORECASE))
    density = (count / len(words)) if words else 0
    # Lunghezza URL
    url_len = len(url_slug)
    # Paragrafo più lungo (SENZA HTML)
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
    max_par_words = 0
    for p in paragraphs:
        p_clean = re.sub(r'<[^>]+>', '', p)
        # Conta solo se c'è almeno una parola vera
        n_words = len(re.findall(r'\w+', p_clean))
        if n_words > max_par_words:
            max_par_words = n_words
    # Se non ci sono paragrafi, max_par_words resta 0
    values = {
        5: f"({wc-1} parole)",
        8: f"({density*100:.2f}% - {count} occorrenze)",
        9: f"({url_len} caratteri)",
        16: f"(max {max_par_words} parole in un paragrafo)",
    }

    not_ok = []
    ok = []
    # Tooltip HTML per la regola power word
    power_words_list = [
        "Incredibile", "Sorprendente", "Scioccante", "Irresistibile", "Ufficiale", "Garantito", "Gratuito", "Leader", "Veloce", "Straordinario", "Meraviglioso", "Sensazionale", "Nuovo", "Innovativo", "Popolare", "Qualità", "Efficace", "Potente", "Esclusivo", "Motivante", "Sicuro", "Unico"
    ]
    power_words_tip = f"""
    <span class='modern-info-wrap'>
      <span class='modern-info-icon' tabindex='0'>?</span>
      <span class='modern-tooltip'><b>Power words consigliate:</b><br>{', '.join(power_words_list)}</span>
    </span>
    """

    # Aggiungi qui il tooltip per paragrafi brevi
    short_paragraphs_tip = """
    <span class='modern-info-wrap'>
      <span class='modern-info-icon' tabindex='0'>?</span>
      <span class='modern-tooltip'>
        <b>Perché usare paragrafi brevi?</b><br>
        Ogni paragrafo (tag <code>&lt;p&gt;</code>) non deve superare 120 parole
        per mantenere la lettura fluida e chiara, soprattutto su mobile.
      </span>
    </span>
    """

    for idx, r in enumerate(results):
        val = values.get(idx, "")
        is_power = RULES[idx]["func"].__name__ == "rule_power_word_in_title"
        is_short = RULES[idx]["func"].__name__ == "rule_short_paragraphs"
        text = f"{r['text']} {val}" if val else r['text']
        is_custom = idx >= len(RANK_MATH_RULES)

        # Scegli il tooltip giusto
        tip_html = ""
        if is_power:
            tip_html = power_words_tip
        elif is_short:
            tip_html = short_paragraphs_tip

        if not r["ok"]:
            label = "🟦" if is_custom else "❌"
            not_ok.append({"text": f"{label} {text}", "tip": tip_html})
        else:
            label = "🟦" if is_custom else "✅"
            ok.append({"text": f"{label} {text}", "tip": tip_html})

    html = css
    for t in not_ok:
        html += f"<div style='position:relative; border:1px solid #e63946; border-radius:10px; padding:12px 44px 12px 14px; margin-bottom:10px; background-color:#f8d7da; color:#721c24; min-height:28px; font-size:16px; font-weight:500; box-shadow:0 2px 8px rgba(230,57,70,0.07); transition:box-shadow 0.2s;'>{t['text']}{t['tip']}</div>"
    for t in ok:
        html += f"<div style='position:relative; border:1px solid #38b000; border-radius:10px; padding:12px 44px 12px 14px; margin-bottom:10px; background-color:#d4edda; color:#155724; min-height:28px; font-size:16px; font-weight:500; box-shadow:0 2px 8px rgba(56,176,0,0.07); transition:box-shadow 0.2s;'>{t['text']}{t['tip']}</div>"
    return html

def update():
    # Recupera i dati correnti dagli input (se disponibili)
    title = st.session_state.get('Titolo SEO', "")
    meta_desc = st.session_state.get('Meta Description (max 160 caratteri)', "")
    url_slug = st.session_state.get('URL Slug (senza dominio)', "")
    content = st.session_state.get("Contenuto dell'articolo", "")
    keyword = st.session_state.get('Keyword principale', "")
    st.session_state['rules_html'] = get_rules_html(title, meta_desc, url_slug, content, keyword)

def auto_complete():
    # Al cambio di keyword, compila Titolo SEO, URL Slug e Contenuto
    kw = st.session_state.get('Keyword principale', '').strip()
    if not kw:
        return
    # Title Case per il titolo
    default_title = capwords(kw)
    if not st.session_state.get('Titolo SEO', '').strip():
        st.session_state['Titolo SEO'] = default_title
    # Slug in minuscolo con trattini
    if not st.session_state.get('URL Slug (senza dominio)', '').strip():
        st.session_state['URL Slug (senza dominio)'] = kw.lower().replace(' ', '-')
    # Ricalcola le regole
    update()

def block_to_html(block):
    t = block["type"]
    if t == "Paragrafo":
        return f"<p>{block['content']}</p>"
    if t == "Titolo H2":
        return f"<h2>{block['content']}</h2>"
    if t == "Immagine":
        url = block.get("url", "")
        alt = block.get("alt", "")
        return f'<img src="{url}" loading="lazy" alt="{alt}" />'
    return ""

def assemble_blocks(blocks):
    # Nessuna indentazione qui!
    return "\n".join(block_to_html(b) for b in blocks)

def scroll_to_editor():
    # Usa uno snippet JS per scrollare in fondo dove c'è l'editor
    components.html("""
        <script>
        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
        </script>
    """, height=0)

# Main UI
def main():
    st.set_page_config(page_title="SEO Article Generator", layout="wide")

    # --- INIZIO SIDEBAR: Salva/Carica bozza ---
    st.sidebar.markdown("### 📄 Gestione Bozze")

    draft_name = st.sidebar.text_input("Nome bozza", value="", placeholder="nome_bozza", key="draft_name")

    bozze_dir = os.path.join(os.getcwd(), "output", "bozze")
    os.makedirs(bozze_dir, exist_ok=True)
    draft_files = [f for f in os.listdir(bozze_dir) if f.endswith(".json")]
    draft_files.sort()

    if draft_files:
        selected_draft = st.sidebar.selectbox("Carica bozza", draft_files, key="selected_draft", index=0)
    else:
        selected_draft = st.sidebar.selectbox("Carica bozza", ["Nessuna bozza disponibile"], key="selected_draft", index=0)

    col_save, col_load = st.sidebar.columns(2)
    with col_save:
        if st.button("💾 Salva bozza", key="save_draft_btn_sidebar"):
            save_draft(os.path.join(bozze_dir, f"{draft_name}.json"))
    with col_load:
        if st.button("📂 Carica bozza", key="load_draft_btn_sidebar") and selected_draft:
            st.session_state["load_draft_pending"] = os.path.join(bozze_dir, selected_draft)
            st.rerun()

    # Mostra il messaggio di salvataggio su tutta la larghezza della sidebar
    if st.session_state.get("last_draft_path"):
        st.sidebar.success(f"Bozza salvata in {st.session_state['last_draft_path']}")
        del st.session_state["last_draft_path"]

    # --- FINE SIDEBAR: Salva/Carica bozza ---

    # Caricamento bozza PRIMA di creare i widget
    pending_draft = st.session_state.get("load_draft_pending", False)
    if pending_draft:
        try:
            with open(pending_draft, "r", encoding="utf-8") as f:
                draft = json.load(f)
            for k, v in draft.items():
                st.session_state[k] = v
            st.success(f"Bozza caricata da {pending_draft}!")
        except Exception as e:
            st.error(f"Errore nel caricamento bozza: {e}")
        st.session_state["load_draft_pending"] = False
        st.rerun()

    # Aggiungi dopo st.set_page_config()
    st.markdown("""
    <script>
    // Funzione che assicura che le etichette .fixed-label restino sempre visibili
    function mantieni_etichette_visibili() {
        const etichette = document.querySelectorAll('.fixed-label');
        etichette.forEach(etichetta => {
            etichetta.style.display = 'block';
            etichetta.style.visibility = 'visible';
            etichetta.style.opacity = '1';
            etichetta.style.position = 'static';
            etichetta.style.pointerEvents = 'auto';
        });
    }

    // Esegui subito e poi ogni 200ms per catturare aggiornamenti dinamici
    document.addEventListener('DOMContentLoaded', function() {
        mantieni_etichette_visibili();
        setInterval(mantieni_etichette_visibili, 200);
    });
    </script>
    """, unsafe_allow_html=True)

    # Inseriamo subito un'ancora invisibile in cima alla pagina.
    st.markdown('<div id="top_anchor"></div>', unsafe_allow_html=True)

    # Ora eseguiamo il resto della logica di inizializzazione.
    if "pending_content" in st.session_state:
        st.session_state["Contenuto dell'articolo"] = st.session_state["pending_content"]
        del st.session_state["pending_content"]

    if st.session_state.get("scroll_to_top_pending", False):
        components.html(
            """
            <script>
                // Aspetta un istante, poi scrolla all'ancora in cima.
                setTimeout(function() {
                    const anchor = window.parent.document.getElementById("top_anchor");
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 150);
            </script>
            """,
            height=0
        )
        del st.session_state.scroll_to_top_pending

    st.markdown('''
    <style>
    /* Minimal modern button style */
    button.stButton > button, div.stButton > button {
        background: #fff;
        color: #1976d2;
        border: 1.5px solid #1976d2;
        border-radius: 8px;
        padding: 0.6em 1.5em;
        font-size: 1.08rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.07);
        transition: background 0.18s, box-shadow 0.18s, color 0.18s, border-color 0.18s;
        outline: none;
        cursor: pointer;
    }
    button.stButton > button:hover, div.stButton > button:hover {
        background: #e3f0fc !important; /* hover: azzurrino chiaro */
        color: #1251a3 !important;
        border-color: #1251a3 !important;
        box-shadow: 0 4px 16px rgba(25, 118, 210, 0.13) !important;
    }
    button.stButton > button:active, div.stButton > button:active {
        background: #c7e0fa !important; /* active: azzurro più intenso */
        color: #0d3c75 !important;
        border-color: #1251a3 !important;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.18) !important;
    }
    button.stButton > button:focus, div.stButton > button:focus {
        outline: none !important;
        background: #fff !important;
        color: #1251a3 !important;
        border-color: #1251a3 !important;
        box-shadow: 0 0 0 2px #e3f0fc !important; /* leggero glow azzurrino, NO doppio bordo */
    }
    /* UNIVERSAL OVERRIDE: forza testo e bordo blu in ogni stato e classe */
    button.stButton > button, div.stButton > button,
    button.stButton > button:active, div.stButton > button:active,
    button.stButton > button:focus, div.stButton > button:focus,
    button.stButton > button[style], div.stButton > button[style],
    button.stButton > button[class], div.stButton > button[class] {
        color: #1251a3 !important;
        border-color: #1251a3 !important;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.13) !important;
        text-shadow: none !important;
    }
    /* Disabilita ogni bordo rosso interno/esterno */
    button.stButton > button:after, button.stButton > button:before,
    div.stButton > button:after, div.stButton > button:before {
        border-color: #1251a3 !important;
        box-shadow: none !important;
    }
    </style>
    ''', unsafe_allow_html=True)
    st.title("Creazione Articolo SEO 100/100 con Rank Math")

    # Sidebar inputs
    st.sidebar.header("Inserisci Parola Chiave Principale")
    
    # Aggiungiamo le etichette fisse che non scompariranno MAI
    st.sidebar.markdown("""
    <style>
    /* STILE ETICHETTE SIDEBAR SEMPRE COERENTE */
    .fixed-label {
        display: block;
        font-size: 14px;
        font-weight: 600;
        color: rgb(49, 51, 63);
        margin: 0 0 0.25rem 0 !important; /* IMPORTANTE: margine fisso */
        padding: 0 !important;
        height: auto !important;
        line-height: 1.4 !important;
    }
    
    /* Uniforma lo spazio tra etichetta e campo in OGNI STATO */
    div[data-testid="stSidebar"] div[data-testid="stTextInput"],
    div[data-testid="stSidebar"] div[data-testid="stTextArea"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
        position: relative !important; /* Importante per il posizionamento assoluto */
    }
    
    /* IMPORTANTE: rimuovi completamente qualsiasi label nativa di Streamlit nella sidebar */
    div[data-testid="stSidebar"] div[data-testid="stTextInput"] label,
    div[data-testid="stSidebar"] div[data-testid="stTextArea"] label {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
        visibility: hidden !important;
    }
    
    /* Garantisci che lo spazio tra elementi della sidebar sia sempre lo stesso */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # PRIMA DELL'INPUT mostriamo l'etichetta fissa
    st.sidebar.markdown("<div class='fixed-label'>Keyword principale</div>", unsafe_allow_html=True)
    keyword = st.sidebar.text_input(
        "",  # Etichetta vuota, usiamo quella personalizzata sopra
        key='Keyword principale',
        on_change=auto_complete
    )
    if not keyword:
        st.sidebar.info("Per proseguire inserisci la parola chiave principale.")
        return

    st.sidebar.header("Parametri Articolo")

    # Titolo SEO + indicatori
    st.sidebar.markdown("<div class='fixed-label'>Titolo SEO</div>", unsafe_allow_html=True)
    title = st.sidebar.text_input(
        "",  # Etichetta vuota
        key='Titolo SEO',
        on_change=update
    )
    title_len = len(st.session_state.get('Titolo SEO',''))
    max_title = 60
    segments = ['#e63946','#fb8c00','#ffeb3b','#cddc39','#38b000']

    # Se supera il massimo, tutte rosse
    if title_len > max_title:
        bar = "<div style='display:flex; margin-top:4px;'>"
        for _ in segments:
            bar += "<div style='flex:1; height:6px; background:#e63946; opacity:1;'></div>"
        bar += "</div>"
    else:
        idx = min(title_len * 5 // (max_title + 1), 4)
        bar = "<div style='display:flex; margin-top:4px;'>"
        for i, col in enumerate(segments):
            bar += f"<div style='flex:1; height:6px; background:{col}; opacity:{1 if i<=idx else 0.3};'></div>"
        bar += "</div>"

    st.sidebar.markdown(bar, unsafe_allow_html=True)
    st.sidebar.markdown(f"<span style='font-size:12px; color:#666;'>{title_len}/{max_title}</span>", unsafe_allow_html=True)

    # URL Slug + indicatori
    st.sidebar.markdown("<div class='fixed-label'>URL Slug (senza dominio)</div>", unsafe_allow_html=True)

    # Parte fissa
    base_url = "https://ti-aiuto.io/"
    end_slash = "/"
    base_len = len(base_url)
    end_len = len(end_slash)

    # Input solo per la parte centrale
    slug = st.sidebar.text_input(
        "",  # Etichetta vuota
        key='URL Slug (senza dominio)',
        on_change=update,
        placeholder="come-installare-windows-11"
    )

    # Mostra il campo con la parte fissa e finale
    st.sidebar.markdown(
        f"<div style='display:flex;align-items:center;font-size:15px;'>"
        f"<span style='color:#888;'>{base_url}</span>"
        f"<input type='text' value='{slug}' style='flex:1;border:1.5px solid #1976d2;border-radius:7px;padding:4px 8px;font-size:15px;' readonly disabled>"
        f"<span style='color:#888;'>{end_slash}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Calcola la lunghezza totale
    slug_len = base_len + len(slug) + end_len
    max_slug = 75
    segments = ['#e63946','#fb8c00','#ffeb3b','#cddc39','#38b000']

    if slug_len > max_slug:
        bar = "<div style='display:flex; margin-top:4px;'>"
        for _ in segments:
            bar += "<div style='flex:1; height:6px; background:#e63946; opacity:1;'></div>"
        bar += "</div>"
    else:
        idx = min(slug_len * 5 // (max_slug + 1), 4)
        bar = "<div style='display:flex; margin-top:4px;'>"
        for i, col in enumerate(segments):
            bar += f"<div style='flex:1; height:6px; background:{col}; opacity:{1 if i<=idx else 0.3};'></div>"
        bar += "</div>"
    st.sidebar.markdown(bar, unsafe_allow_html=True)
    st.sidebar.markdown(f"<span style='font-size:12px; color:#666;'>{slug_len}/{max_slug}</span>", unsafe_allow_html=True)

    # Meta Description + indicatori
    st.sidebar.markdown("<div class='fixed-label'>Meta Description (max 160 caratteri)</div>", unsafe_allow_html=True)
    meta_desc = st.sidebar.text_area(
        "",  # Etichetta vuota
        key='Meta Description (max 160 caratteri)',
        height=100,
        on_change=update
    )
    meta_len = len(st.session_state.get('Meta Description (max 160 caratteri)',''))
    max_meta = 160
    if meta_len > max_meta:
        bar = "<div style='display:flex; margin-top:4px;'>"
        for _ in segments:
            bar += "<div style='flex:1; height:6px; background:#e63946; opacity:1;'></div>"
        bar += "</div>"
    else:
        idx = min(meta_len * 5 // (max_meta + 1), 4)
        bar = "<div style='display:flex; margin-top:4px;'>"
        for i, col in enumerate(segments):
            bar += f"<div style='flex:1; height:6px; background:{col}; opacity:{1 if i<=idx else 0.3};'></div>"
        bar += "</div>"
    st.sidebar.markdown(bar, unsafe_allow_html=True) # <-- CORREZIONE
    st.sidebar.markdown(f"<span style='font-size:12px; color:#666;'>{meta_len}/{max_meta}</span>", unsafe_allow_html=True) # <-- CORREZIONE

    # Il contenuto ora è gestito solo dall'editor, quindi lo recuperiamo dallo stato
    content = assemble_blocks(st.session_state.get("content_blocks", []))

    # Layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Anteprima Articolo")
        st.markdown(generate_html(title, meta_desc, slug, content), unsafe_allow_html=True)
        st.markdown("---")
        
        # Scegli il contenuto giusto per le regole:
    content_for_rules = assemble_blocks(st.session_state.get("content_blocks", []))
    # Genera il codice HTML finale WordPress
    final_html = generate_wp_article_block(title, meta_desc, content_for_rules)

    # Passa sempre final_html alle regole:
    rules_results = check_all_rules(title, meta_desc, slug, final_html, keyword)
    rules_html = get_rules_html(title, meta_desc, slug, final_html, keyword)

    total_rules = len(rules_results)
    respected = sum(1 for r in rules_results if r["ok"])
    not_respected = total_rules - respected

    st.markdown(
        f"""<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;">
            <span style="font-size:1.45em;font-weight:700;letter-spacing:-1px;">
                Regole da rispettare:
            </span>
            <span style="display:flex;align-items:center;gap:18px;">
                <span style="background:#e8f5e9;padding:7px 18px;border-radius:18px;font-size:1.15em;font-weight:700;color:#38b000;box-shadow:0 2px 8px rgba(56,176,0,0.07);">
                    {respected}
                    <span style="color:#888;font-weight:500;">/</span>
                    <span style="color:#1976d2;">{total_rules}</span>
                </span>
                <span style="background:#fdeaea;padding:7px 16px 7px 14px;border-radius:18px;font-size:1.08em;font-weight:600;color:#e63946;box-shadow:0 2px 8px rgba(230,57,70,0.07);">
                    Mancanti: <span style="font-weight:700;">{not_respected}</span>
                </span>
            </span>
        </div>""",
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # Passa final_html a get_rules_html!
    rules_html = get_rules_html(title, meta_desc, slug, final_html, keyword)
    st.markdown(rules_html, unsafe_allow_html=True)

    with col2:
        st.markdown("### Codice HTML da incollare su WordPress")
        st.code(final_html, language='html')

    # --- MODAL LOGIC START ---
    def check_article_params():
        missing = []
        # Titolo SEO
        title = st.session_state.get('Titolo SEO', "").strip()
        title_len = len(title)
        max_title = 60
        if not title:
            missing.append("Titolo (mancante)")
        else:
            idx = min(title_len * 5 // (max_title + 1), 4)
            if idx != 4:
                missing.append("Titolo (non ottimale)")
        # URL Slug
        url_slug = st.session_state.get('URL Slug (senza dominio)', "").strip()
        base_url = "https://ti-aiuto.io/"
        end_slash = "/"
        base_len = len(base_url)
        end_len = len(end_slash)
        slug_len = base_len + len(url_slug) + end_len  # <-- CORREZIONE QUI
        max_slug = 75
        if not url_slug:
            missing.append("URL Slug (mancante)")
        else:
            idx = min(slug_len * 5 // (max_slug + 1), 4)
            if idx != 4:
                missing.append("URL Slug (non ottimale)")
        # Meta Description
        meta_desc = st.session_state.get('Meta Description (max 160 caratteri)', "").strip()
        meta_len = len(meta_desc)
        max_meta = 160
        if not meta_desc:
            missing.append("Meta Description (mancante)")
        else:
            idx = min(meta_len * 5 // (max_meta + 1), 4)
            if idx != 4:
                missing.append("Meta Description (non ottimale)")
        # Contenuto
        content = assemble_blocks(st.session_state.get("content_blocks", []))
        if not content.strip():
            missing.append("Contenuto (mancante)")
        return missing

    def check_all_rules_status():
        results = check_all_rules(title, meta_desc, slug, final_html, keyword)
        return [r for r in results if not r["ok"]]

    if "show_save_modal" not in st.session_state:
        st.session_state.show_save_modal = False
    if "force_save" not in st.session_state:
        st.session_state.force_save = False
    if "save_error" not in st.session_state:
        st.session_state.save_error = ""
    if "last_save_path" not in st.session_state:
        st.session_state.last_save_path = ""

    if st.session_state.get("show_save_modal", False) and 'show_save_modal_id' not in st.session_state:
        st.session_state['show_save_modal_id'] = str(uuid.uuid4())

    if st.button("Crea articolo HTML", on_click=update):
        st.session_state.save_error = ""
        st.session_state.last_save_path = ""
        st.session_state.force_save = False
        st.session_state.show_save_modal = True

    if st.session_state.get("show_save_modal", False):
        missing = check_article_params()
        not_ok = check_all_rules_status()
        n_missing = len(missing)
        n_not_ok = len(not_ok)
        proceed = True

        if n_missing > 0 or n_not_ok > 0:
            st.warning(f"⚠️ {n_not_ok} regole non rispettate, {n_missing} parametri da sistemare.")
            if n_missing > 0:
                st.markdown(f"**Parametri da sistemare:** {', '.join(missing)}")
            if n_not_ok > 0:
                st.markdown("**Regole non rispettate:**")
                for r in not_ok:
                    st.markdown(f"- {r['text']}")

            checkbox_key = "force_save_checkbox"
            proceed = st.checkbox("Procedi comunque?", key=checkbox_key)

        if n_missing == 0 and n_not_ok == 0:
            st.success("Tutte le regole e i parametri sono a posto!")
        if n_missing == 0 or proceed:
            filename = st.text_input("Nome file (senza estensione)", key="save_filename")
            if st.button("Salva articolo", key="save_confirm_btn"):
                slug_name = filename.strip() or url_slug or 'articolo'
                articoli_dir = os.path.join(os.getcwd(), "output", "articoli")
                os.makedirs(articoli_dir, exist_ok=True)
                full_path = os.path.join(articoli_dir, f"{slug_name}.html")

                if os.path.exists(full_path):
                    st.error(f"❌ Il file esiste già: {full_path}. Scegli un altro nome.")
                else:
                    try:
                        # Salva solo il codice WordPress
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(final_html)
                        st.session_state.last_save_path = full_path
                        st.session_state.save_error = ""
                        st.success(f"✅ File salvato in: {full_path}")
                    except Exception as e:
                        st.session_state.save_error = f"❌ Errore durante il salvataggio: {e}"

        if st.session_state.save_error:
            st.error(st.session_state.save_error)

        if st.session_state.last_save_path:
            if st.button("Chiudi", key="close_modal_btn"):
                st.session_state.show_save_modal = False
                st.session_state.save_error = ""
                st.session_state.last_save_path = ""
                if "force_save_checkbox" in st.session_state:
                    del st.session_state["force_save_checkbox"]
                st.rerun()
        # Pulsante Annulla per chiudere la modale
        elif not st.session_state.last_save_path:
            if st.button("Annulla", key="cancel_save_modal"):
                st.session_state.show_save_modal = False
                st.session_state.save_error = ""
                st.session_state.last_save_path = ""
                if "force_save_checkbox" in st.session_state:
                    del st.session_state["force_save_checkbox"]
                st.rerun()
    # --- MODAL LOGIC END ---

    # Bottone per aprire/chiudere l’Editor Contenuto
    if not st.session_state.get("show_content_editor", False):
        if st.sidebar.button("Apri Editor Contenuto"):
            st.session_state.show_content_editor = True
            st.session_state.scroll_to_editor_pending = True
            st.rerun()
    else:
        if st.sidebar.button("Chiudi Editor Contenuto"):
            # Salva il contenuto corrente come fa "Salva e Chiudi"
            st.session_state["pending_content"] = st.session_state.raw_content_html
            if "show_content_editor" in st.session_state:
                del st.session_state.show_content_editor
            st.session_state.scroll_to_top_pending = True
            st.rerun()

    # Se devo mostrare l’editor…
    if st.session_state.get("show_content_editor", False):
        # 1) metto un anchor HTML
        st.markdown('<div id="editor_anchor"></div>', unsafe_allow_html=True)

        # 2) se è pending, scrollo a quell’anchor
        if st.session_state.get("scroll_to_editor_pending", False):
            components.html(
                """
                <script>
                    // Aspetta 150ms per dare tempo alla pagina di renderizzare tutto.
                    setTimeout(function() {
                        // Cerca l'ancora sulla PAGINA PRINCIPALE (window.parent)
                        // e non nel box isolato dello script. QUESTA è la correzione.
                        const anchor = window.parent.document.getElementById("editor_anchor");
                        if (anchor) {
                            anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }, 150);
                </script>
                """,
                height=0
            )
            del st.session_state["scroll_to_editor_pending"]

        # 3) quindi mostro l’expander con l’editor
        with st.expander("Editor Contenuto", expanded=True):
            # Cambia da [1,2,1] a [1.3,1.7,1] per dare più spazio a Blocchi Contenuto
            cols = st.columns([1.3,1.7,1], gap="small")

            # Colonna SX: lista blocchi + drag‐n‐drop
            with cols[0]:
                st.subheader("Blocchi contenuto")
                # NON aggiungere più un paragrafo di default quando si apre l'editor
                if "content_blocks" not in st.session_state:
                    st.session_state.content_blocks = []
                if "raw_content_html" not in st.session_state:
                    st.session_state.raw_content_html = ""

                blocks = st.session_state.content_blocks
                st.markdown("""
                <style>
                .add-block-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 7px;
                    background: #f7f7fa;
                    color: #1976d2;
                    border: 1.5px solid #1976d2;
                    border-radius: 7px;
                    padding: 0.38em 1.1em;
                    font-size: 1.07rem;
                    font-weight: 600;
                    margin-right: 10px;
                    margin-bottom: 8px;
                    cursor: pointer;
                    transition: background 0.18s, color 0.18s, border-color 0.18s;
                    box-shadow: 0 1px 4px rgba(25,118,210,0.04);
                }
                .add-block-btn:hover {
                    background: #e3f0fc;
                    color: #1251a3;
                    border-color: #1251a3;
                }
                .add-block-btn svg {
                    width: 1.2em;
                    height: 1.2em;
                    vertical-align: middle;
                }
                </style>
                """, unsafe_allow_html=True)

                col_btn1, col_btn2, col_btn3 = st.columns([1,1,1], gap="small")
                with col_btn1:
                    if st.button("📝 Paragrafo", key="add_paragraph", help="Aggiungi un paragrafo", use_container_width=True):
                        blocks.append({"type": "Paragrafo", "content": ""})
                        st.session_state.content_blocks = blocks
                        st.rerun()
                with col_btn2:
                    if st.button("🔠 Titolo H2", key="add_h2", help="Aggiungi un titolo H2", use_container_width=True):
                        blocks.append({"type": "Titolo H2", "content": ""})
                        st.session_state.content_blocks = blocks
                        st.rerun()
                with col_btn3:
                    if st.button("🖼️ Immagine", key="add_image", help="Aggiungi un'immagine", use_container_width=True):
                        blocks.append({"type": "Immagine", "url": "", "alt": ""})
                        st.session_state.content_blocks = blocks
                        st.rerun()

                st.markdown("""
                <style>
                /* AGGIUNGI questa regola all'inizio dell'editor CSS per forzare le etichette della sidebar */
                div[data-testid="stSidebar"] .fixed-label {
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    padding-bottom: 0 !important;
                    padding-top: 2px;
                    border-radius: 6px;
                    background: #f7f7fa;
                    box-shadow: 0 1px 4px rgba(25,118,210,0.04);
                }
                /* togli gap tra label e widget successivo */
                .compact-block-row + div {
                    margin-top: 0 !important;
                    padding-top: 0 !important;
                }
                /* rimuovi eventuali margini delle etichette vuote */
                div[data-testid="stTextInput"] label,
                div[data-testid="stTextArea"] label {
                    display: none !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                /* forza il widget senza margine superiore */
                div[data-testid="stTextInput"],
                div[data-testid="stTextArea"] {
                    margin-top: 0 !important;
                    padding-top: 0 !important;
                }

                div[data-testid="stExpanderContent"] button[kind="secondary"]:hover {
                    background: #eeeeee !important;
                    color: #555555 !important;
                    border-color: #aaaaaa !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # Blocchi compatti con frecce a sinistra
                for i, blk in enumerate(blocks):
                    col_arrow, col_content = st.columns([0.18, 0.82])
                    with col_arrow:
                        st.markdown("""
                        <style>
                        .editor-btn {
                            width: 38px;
                            height: 38px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.25em;
                            background: #f7f7fa;
                            color: #1976d2;
                            border: 1.5px solid #1976d2;
                            border-radius: 7px;
                            cursor: pointer;
                            transition: background 0.18s, color 0.18s, border-color 0.18s;
                            font-weight: bold;
                            padding: 0;
                            margin-bottom: 6px;
                        }
                        .editor-btn:hover, .editor-btn:active, .editor-btn:focus {
                            background: #e3f0fc !important;
                            color: #1251a3 !important;
                            border-color: #1251a3 !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        btns = st.columns(1, gap="small")
                        with btns[0]:
                            arrow_up = st.button("↑", key=f"up_{i}", help="Sposta su", use_container_width=True)
                            arrow_down = st.button("↓", key=f"down_{i}", help="Sposta giù", use_container_width=True)
                            delete = st.button("✖", key=f"del_{i}", help="Elimina blocco", use_container_width=True)

                        # Gestione spostamento
                        if arrow_up and i > 0:
                            blocks[i-1], blocks[i] = blocks[i], blocks[i-1]
                            st.session_state.content_blocks = blocks
                            st.rerun()
                        if arrow_down and i < len(blocks)-1:
                            blocks[i], blocks[i+1] = blocks[i+1], blocks[i]
                            st.session_state.content_blocks = blocks
                            st.rerun()
                        # Gestione eliminazione
                        if delete:
                            blocks.pop(i)
                            st.session_state.content_blocks = blocks
                            st.rerun()

                    with col_content:
                        # Elemento compatto: titolo + box input tutto attaccato
                        imported_label = " [importato]" if blk.get("imported") else ""
                        st.markdown(
                            f"<div class='compact-block-row'><b>{i+1}. {blk['type']}{imported_label}</b></div>",
                            unsafe_allow_html=True
                        )
                        if blk["type"] == "Paragrafo":
                            pending_key = f"pending_txt_{i}"
                            if pending_key in st.session_state:
                                st.session_state[f"txt_{i}"] = st.session_state[pending_key]
                                blk["content"] = st.session_state[pending_key]
                                del st.session_state[pending_key]
                            else:
                                blk["content"] = st.session_state.get(f"txt_{i}", blk["content"])

                            # Ora crea il widget UNA SOLA VOLTA
                            blk["content"] = st.text_area("", blk["content"], key=f"txt_{i}", height=40)
                            # Pulsanti in linea, tutti uguali
                            st.markdown("""
                            <style>
                            .editor-btn-row {
                                display: flex;
                                gap: 8px;
                                margin-bottom: 8px;
                            }
                            .editor-btn {
                                width: 38px;
                                height: 38px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 1.25em;
                                background: #f7f7fa;
                                color: #1976d2;
                                border: 1.5px solid #1976d2;
                                border-radius: 7px;
                                cursor: pointer;
                                transition: background 0.18s, color 0.18s, border-color 0.18s;
                                font-weight: bold;
                                padding: 0;
                            }
                            .editor-btn:hover, .editor-btn:active, .editor-btn:focus {
                                background: #e3f0fc !important;
                                color: #1251a3 !important;
                                border-color: #1251a3 !important;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            btn_cols = st.columns(6, gap="small")
                            with btn_cols[0]:
                                st.button("💻", key=f"code_{i}", help="Inserisci <code>", on_click=insert_tag_in_text, args=("<code>", "</code>", f"txt_{i}"), use_container_width=True)
                            with btn_cols[1]:
                                st.button("𝐁", key=f"strong_{i}", help="Inserisci <strong>", on_click=insert_tag_in_text, args=("<strong>", "</strong>", f"txt_{i}"), use_container_width=True)
                            with btn_cols[2]:
                                st.button("🗒️", key=f"ul_{i}", help="Inserisci elenco puntato", on_click=insert_tag_in_text, args=("<ul><li>", "</li></ul>", f"txt_{i}"), use_container_width=True)
                            with btn_cols[3]:
                                st.button("🔗", key=f"dofollow_{i}", help="Inserisci link DoFollow", on_click=insert_dofollow_link, args=(f"txt_{i}",), use_container_width=True)
                            with btn_cols[4]:
                                st.button("🚫", key=f"nofollow_{i}", help="Inserisci link NoFollow", on_click=insert_nofollow_link, args=(f"txt_{i}",), use_container_width=True)
                            with btn_cols[5]:
                                st.button("🏠", key=f"internal_{i}", help="Inserisci link interno", on_click=insert_internal_link, args=(f"txt_{i}",), use_container_width=True)

                        elif blk["type"] == "Titolo H2":
                            pending_key = f"pending_h2_{i}"
                            if pending_key in st.session_state:
                                blk["content"] = st.session_state[pending_key]
                                st.session_state[f"h2_{i}"] = st.session_state[pending_key]
                                del st.session_state[pending_key]
                            else:
                                blk["content"] = st.session_state.get(f"h2_{i}", blk["content"])

                            blk["content"] = st.text_input("", blk["content"], key=f"h2_{i}")
                            # Pulsanti in linea, tutti uguali
                            st.markdown("""
                            <style>
                            .editor-btn-row {
                                display: flex;
                                gap: 8px;
                                margin-bottom: 8px;
                            }
                            .editor-btn {
                                width: 38px;
                                height: 38px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 1.25em;
                                background: #f7f7fa;
                                color: #1976d2;
                                border: 1.5px solid #1976d2;
                                border-radius: 7px;
                                cursor: pointer;
                                transition: background 0.18s, color 0.18s, border-color 0.18s;
                                font-weight: bold;
                                padding: 0;
                            }
                            .editor-btn:hover, .editor-btn:active, .editor-btn:focus {
                                background: #e3f0fc !important;
                                color: #1251a3 !important;
                                border-color: #1251a3 !important;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            btn_cols = st.columns(6, gap="small")
                            with btn_cols[0]:
                                st.button("💻", key=f"code_h2_{i}", help="Inserisci <code>", on_click=insert_tag_in_text, args=("<code>", "</code>", f"h2_{i}"), use_container_width=True)
                            with btn_cols[1]:
                                st.button("𝐁", key=f"strong_h2_{i}", help="Inserisci <strong>", on_click=insert_tag_in_text, args=("<strong>", "</strong>", f"h2_{i}"), use_container_width=True)
                            with btn_cols[2]:
                                st.button("🗒️", key=f"ul_h2_{i}", help="Inserisci elenco puntato", on_click=insert_tag_in_text, args=("<ul><li>", "</li></ul>", f"h2_{i}"), use_container_width=True)
                            with btn_cols[3]:
                                st.button("🔗", key=f"dofollow_h2_{i}", help="Inserisci link DoFollow", on_click=insert_dofollow_link, args=(f"h2_{i}",), use_container_width=True)
                            with btn_cols[4]:
                                st.button("🚫", key=f"nofollow_h2_{i}", help="Inserisci link NoFollow", on_click=insert_nofollow_link, args=(f"h2_{i}",), use_container_width=True)
                            with btn_cols[5]:
                                st.button("🏠", key=f"internal_h2_{i}", help="Inserisci link interno", on_click=insert_internal_link, args=(f"h2_{i}",), use_container_width=True)
                        else:  # Immagine
                            st.markdown("""
                            <style>
                            .img-info-wrap {
                                display: inline-flex;
                                align-items: center;
                                margin-left: 6px;
                                position: relative;
                            }
                            .img-info-icon {
                                display: inline-block;
                                width: 18px;
                                height: 18px;
                                line-height: 18px;
                                text-align: center;
                                border-radius: 50%;
                                background: #e0e0e0;
                                font-size: 0.95em;
                                cursor: help;
                                margin-left: 2px;
                                color: #1976d2;
                                font-weight: bold;
                            }
                            .img-info-wrap .img-tooltip {
                                visibility: hidden;
                                opacity: 0;
                                width: 220px;
                                background-color: #333;
                                color: #fff;
                                text-align: left;
                                padding: 8px;
                                border-radius: 4px;
                                position: absolute;
                                z-index: 1;
                                bottom: 125%;
                                left: 50%;
                                transform: translateX(-50%);
                                transition: opacity 0.2s;
                                font-size: 0.98em;
                            }
                            .img-info-wrap:hover .img-tooltip {
                                visibility: visible;
                                opacity: 1;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            url = st.text_input("", blk.get("url", ""), key=f"img_url_{i}", placeholder="https://...")
                            alt = st.text_input("", blk.get("alt", ""), key=f"img_alt_{i}", placeholder="Alt text")
                            blk["url"], blk["alt"] = url, alt
                st.session_state.content_blocks = blocks

                # Aggiorna l'HTML solo se non è stato modificato manualmente
                if not st.session_state.get("raw_editor_active", False):
                    st.session_state.raw_content_html = assemble_blocks(blocks)

            # Colonna CENTRALE: preview renderizzata
            with cols[1]:
                st.subheader("Anteprima Contenuto")
                preview_html = assemble_blocks(st.session_state.content_blocks)
                st.markdown(preview_html, unsafe_allow_html=True)

            # Colonna DX: editor HTML
            with cols[2]:
                st.subheader("HTML Contenuto")
                st.text_area(
                    "Anteprima HTML",
                    assemble_blocks(st.session_state.content_blocks),
                    height=400,
                    key="raw_content_html",
                    disabled=True
                )

                st.markdown("#### Incolla qui l'HTML da importare")
                # RESET: azzera il box se serve
                if st.session_state.get("import_html_box_reset", False):
                    st.session_state["import_html_box"] = ""
                    st.session_state["import_html_box_reset"] = False

                import_html = st.text_area(
                    "HTML da importare",
                    "",
                    height=180,
                    key="import_html_box"
                )

                if st.button("Importa blocchi da HTML", key="import_blocks_btn"):
                    imported_blocks = import_blocks_from_html(import_html, st.session_state.content_blocks)
                    if imported_blocks:
                        for b in imported_blocks:
                            st.session_state.content_blocks.append(b)
                        st.session_state["import_html_box_reset"] = True  # segnala reset per il prossimo rerun
                        st.success(f"{len(imported_blocks)} nuovi blocchi importati!")
                        st.rerun()
                    else:
                        st.warning("Nessun nuovo blocco trovato nell'HTML!")

            # Pulsante Salva e Chiudi (chiude anche la sezione e scrolla in cima)
            if st.button("Salva e Chiudi", key="close_editor"):
                st.session_state["pending_content"] = st.session_state.raw_content_html
                del st.session_state.show_content_editor
                st.session_state.scroll_to_top_pending = True
                st.rerun()

    # Continua con il resto del tuo main (preview articolo, regole, modal save article, ecc.)…
def insert_tag_in_text(tag_open, tag_close, key):
    text = st.session_state.get(key, "")
    new_text = text + tag_open + tag_close
    st.session_state[f"pending_{key}"] = new_text

def insert_dofollow_link(key):
    # Inserisce un link DoFollow di esempio
    text = st.session_state.get(key, "")
    new_text = text + '<a href="https://www.esempio.com" rel="dofollow">Testo Link</a>'
    st.session_state[f"pending_{key}"] = new_text

def insert_nofollow_link(key):
    text = st.session_state.get(key, "")
    new_text = text + '<a href="https://www.esempio.com" rel="nofollow">Testo Link</a>'
    st.session_state[f"pending_{key}"] = new_text

def insert_internal_link(key):
    text = st.session_state.get(key, "")
    new_text = text + '<a href="/pagina-interna">Link interno</a>'
    st.session_state[f"pending_{key}"] = new_text

def insert_selected_link(key, link_type):
    text = st.session_state.get(key, "")
    if link_type == "Esterno DoFollow":
        new_text = text + '<a href="https://www.esempio.com" rel="dofollow">Testo Link</a>'
    elif link_type == "Esterno NoFollow":
        new_text = text + '<a href="https://www.esempio.com" rel="nofollow">Testo Link</a>'
    elif link_type == "Interno":
        new_text = text + '<a href="/pagina-interna">Link interno</a>'
    else:
        new_text = text
    st.session_state[f"pending_{key}"] = new_text

def count_words_no_html(text):
    # Rimuovi tutti i tag HTML
    text = re.sub(r'<[^>]+>', '', text)
    # Rimuovi spazi multipli
    text = re.sub(r'\s+', ' ', text).strip()
    return len(re.findall(r"\w+", text))

def import_blocks_from_html(html, existing_blocks):
    # Trova tutti i blocchi <h2>, <p>, <img ...>
    pattern = r'(<h2[^>]*>.*?</h2>)|(<p[^>]*>.*?</p>)|(<img [^>]+>)'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    new_blocks = []
    for h2, p, img in matches:
        if h2:
            content = re.sub(r'<\/?h2[^>]*>', '', h2).strip()
            # Evita duplicati: cerca Titolo H2 con stesso contenuto
            if not any(b["type"] == "Titolo H2" and b.get("content", "").strip() == content for b in existing_blocks):
                new_blocks.append({"type": "Titolo H2", "content": content, "imported": True})
        elif p:
            content = re.sub(r'<\/?p[^>]*>', '', p).strip()
            # Evita duplicati: cerca Paragrafo con stesso contenuto

            if not any(b["type"] == "Paragrafo" and b.get("content", "").strip() == content for b in existing_blocks):
                new_blocks.append({"type": "Paragrafo", "content": content, "imported": True})
        elif img:
            url_match = re.search(r'src=["\']([^"\']+)["\']', img)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img)
            url = url_match.group(1) if url_match else ""
            alt = alt_match.group(1) if alt_match else ""
            # Evita duplicati: cerca Immagine con stesso url e alt
            if not any(b["type"] == "Immagine" and b.get("url", "") == url and b.get("alt", "") == alt for b in existing_blocks):
                new_blocks.append({"type": "Immagine", "url": url, "alt": alt, "imported": True})
    return new_blocks

def save_draft(filename="bozza_articolo.json"):
    draft = {
        "content_blocks": st.session_state.get("content_blocks", []),
        "Titolo SEO": st.session_state.get("Titolo SEO", ""),
        "Meta Description (max 160 caratteri)": st.session_state.get("Meta Description (max 160 caratteri)", ""),
        "URL Slug (senza dominio)": st.session_state.get("URL Slug (senza dominio)", ""),
        "Keyword principale": st.session_state.get("Keyword principale", ""),
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    st.session_state["last_draft_path"] = filename

def load_draft(filename="bozza_articolo.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            draft = json.load(f)
        for k, v in draft.items():
            st.session_state[k] = v
        st.success("Bozza caricata!")
        st.rerun()
    except Exception as e:
        st.error(f"Errore nel caricamento bozza: {e}")

if __name__ == "__main__":
    main()