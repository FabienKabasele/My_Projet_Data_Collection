import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from requests import get
import base64
from streamlit.components.v1 import html
import time

# Configuration de l'application
st.set_page_config(layout="wide", page_title="CoinAfrique Animal Scraper")

# CSS personnalisé
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #d4edda; width: 300px !important; }
    .stApp { background-color: #e6f3ff; }
    .header-section { background-color: #e6f3ff; padding: 20px; }
    .data-section { padding: 20px; }
    .stButton>button { width: 100%; margin: 5px 0; }
    .stSelectbox, .stNumberInput { margin-bottom: 15px; }
    .scraping-progress { margin-top: 20px; }
    .warning-box { background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }
    .form-container { height: 600px; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

# URLs des catégories
CATEGORIES = {
    "Chiens": "chiens",
    "Moutons": "moutons",
    "Poules/Lapins/Pigeons": "poules-lapins-et-pigeons",
    "Autres animaux": "autres-animaux"
}

# URL du formulaire SurveyCTO
SURVEYCTO_FORM_URL = "https://posaf.surveycto.com/collect/evaluation_app?caseid="

def embed_surveycto_form():
    """Intègre le formulaire SurveyCTO via iframe"""
    iframe_code = f"""
    <div class="form-container">
        <iframe src="{SURVEYCTO_FORM_URL}" 
                width="100%" 
                height="600px" 
                frameborder="0" 
                marginheight="0" 
                marginwidth="0"
                allow="geolocation *; microphone *">
            Chargement du formulaire...
        </iframe>
    </div>
    """
    html(iframe_code, height=600)

# Fonction de scraping 
def scrape_category(category, pages):
    df = pd.DataFrame()
    base_url = 'https://sn.coinafrique.com/categorie/'
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for p in range(1, pages + 1):
        status_text.text(f"Scraping {category} - Page {p}/{pages}...")
        progress_bar.progress(p/pages)
        
        url = f'{base_url}{CATEGORIES[category]}?page={p}'
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            containers = soup.find_all('div', class_='col s6 m4 l3')

            data = []
            for container in containers:
                try:
                    nom_tag = container.find('a', class_='card-image')
                    nom = nom_tag['title'].strip() if nom_tag and 'title' in nom_tag.attrs else "N/A"
                    
                    prix_tag = container.find('p', class_='ad_card-price')
                    prix = prix_tag.get_text(strip=True) if prix_tag else container.find('span', class_='btn-floating')['data-ad-price'] + ' FCFA'
                    
                    localisation = container.select_one('p.ad__card-location > span').text.strip()
                    
                    img_tag = container.find('img', class_='ad_card-image')
                    image_link = img_tag['src'] if img_tag else "N/A"

                    data.append({
                        'Nom': nom,
                        'Prix': prix,
                        'Localisation': localisation,
                        'Image_lien': image_link,
                        'Catégorie': category
                    })
                except Exception as e:
                    st.warning(f"Erreur sur une annonce : {e}")
                    continue

            page_df = pd.DataFrame(data)
            df = pd.concat([df, page_df], axis=0).reset_index(drop=True)
            time.sleep(1)  # Respect du politeness

        except Exception as e:
            st.error(f"Erreur page {p}: {e}")
            continue
    
    progress_bar.empty()
    status_text.text(f"Scraping terminé ! {len(df)} annonces trouvées.")
    return df

# Fonction de nettoyage (identique à votre version)
def clean_data(df):
    """Nettoie les données et supprime les colonnes non disponibles"""
    df_clean = df.copy()
    
    # Nettoyage des prix
    df_clean['Prix_num'] = df_clean['Prix'].str.extract('(\d+)')[0].astype(float)
    
    # Standardisation des localisations
    df_clean['Localisation'] = df_clean['Localisation'].str.upper().str.strip()
    
    # Suppression des colonnes vides ou non disponibles
    colonnes_a_supprimer = [col for col in df_clean.columns 
                          if df_clean[col].astype(str).str.strip().isin(["N/A", ""]).all()]
    
    if colonnes_a_supprimer:
        with st.expander(" Nettoyage appliqué", expanded=False):
            st.markdown(f'<div class="warning-box">Colonnes supprimées (données non disponibles): <strong>{", ".join(colonnes_a_supprimer)}</strong></div>', 
                       unsafe_allow_html=True)
        df_clean = df_clean.drop(columns=colonnes_a_supprimer)
    
    return df_clean

# Fonction de téléchargement 
def get_download_link(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Télécharger {filename}</a>'


with st.sidebar:
    st.title("Dashboard")
    
    with st.expander(" Configuration", expanded=True):
        selected_cat = st.selectbox("Catégorie", list(CATEGORIES.keys()))
        page_count = st.number_input("Nombre de pages", 1, 50, 3)
        
    with st.expander(" Données", expanded=True):
        
        data_type = st.selectbox("Type de données", ["Brutes", "Nettoyées"])
        
    with st.expander(" Formulaire", expanded=True):
        
        form_choice = st.selectbox(
            "Choisir un formulaire", 
            ["Contact", "Evaluation de l'apllication"]
        )
        
        # Formulaire de contact 
        if form_choice == "Contact":
            with st.form(key='contact_form'):
                st.text_input("Nom")
                st.text_input("Email")
                rating = st.slider("Évaluation", 1, 5, 3)
                submitted = st.form_submit_button("Envoyer")
                if submitted:
                    st.success("Merci pour votre feedback!")

# Contenu principal
st.markdown('<div class="header-section">', unsafe_allow_html=True)
st.title("DEVOIR DE DATA COLLECTION")
st.markdown("MFUAMBA KABASELE Fabien")
st.markdown("MASTER 1 IA")
st.markdown("Scraping des annonces animales de CoinAfrique Sénégal")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="data-section">', unsafe_allow_html=True)


if 'form_choice' in locals() and form_choice == "Evaluation de l'apllication":
    st.subheader(" Formulaire d'évaluation")
    embed_surveycto_form()
else:
    
    if st.button(f"Scraper {selected_cat} ({page_count} pages)"):
        with st.spinner(f"Scraping en cours pour {selected_cat}..."):
            df_raw = scrape_category(selected_cat, page_count)
            st.session_state.df_raw = df_raw
            st.session_state.df_clean = clean_data(df_raw)

    if 'df_raw' in st.session_state:
        df = st.session_state.df_clean if data_type == "Nettoyées" else st.session_state.df_raw
        
        st.subheader(" Dashboard")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nombre d'annonces", len(df))
        
        with col2:
            avg_price = df['Prix_num'].mean() if 'Prix_num' in df.columns else 0
            st.metric("Prix moyen", f"{avg_price:,.0f} FCFA" if avg_price > 0 else "N/A")
        
        with col3:
            st.metric("Catégorie", selected_cat)
        
        st.subheader("Répartition par localisation")
        st.bar_chart(df['Localisation'].value_counts().head(10))
        
        st.subheader(" Données complètes")
        if data_type == "Nettoyées":
            df_display = df.dropna(axis=1, how='all')
            if df.shape[1] != df_display.shape[1]:
                st.info("Les colonnes entièrement vides ont été masquées")
        else:
            df_display = df
        
        st.dataframe(df_display.drop('Prix_num', axis=1, errors='ignore'))
        
        st.markdown(get_download_link(df, f"coinafrique_{selected_cat}_{data_type.lower()}"), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)