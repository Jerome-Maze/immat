import streamlit as st
import requests
import os
from pathlib import Path
from base64 import b64encode
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="SIV Checker",
    page_icon="🚗",   # ou "assets/logo.png"
    layout="centered"
)

TEST_MODE = False   # Mettre à True pour activer les données de test sans token

#  # Titre de l'application
# st.title("Retrouvez quelle voiture c'était !")
#  # Champ de saisie pour la plaque
# plaque = st.text_input("Entrez le numéro d'une plaque", placeholder="Exemple : AB123CD")

# --- STYLE CARTE GRISE ---
st.markdown("""
<style>
.header-box {
    background: #eef0f4;
    background-image:
        repeating-linear-gradient(
            45deg,
            rgba(255,255,255,0.6) 0,
            rgba(255,255,255,0.6) 2px,
            rgba(230,230,230,0.6) 3px,
            rgba(230,230,230,0.6) 5px
        );
    border: 1px solid #c4c4c4;
    padding: 26px 24px;
    border-radius: 14px;
    margin: 10px 0 26px 0;
    box-shadow: 0 5px 12px rgba(0,0,0,0.1);
    text-align: center;
}
.header-box img {
    width: 360px;
    margin-bottom: 12px;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

#--- Conversion de l'image plaque en base64 ---
def img_src_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + b64encode(f.read()).decode("utf-8")

# Chemin relatif depuis ton fichier .py
PLAQUE_IMG = Path("Data/images/plaque_immat.png")
if not PLAQUE_IMG.exists():
    st.warning(f"Image introuvable : {PLAQUE_IMG.resolve()}")

# --- CONTENEUR HTML ENTIER : image + H1 + texte + input ---
img_src = img_src_base64(PLAQUE_IMG) if PLAQUE_IMG.exists() else ""

st.markdown(f"""
<div class="header-box">
    {'<img src="'+img_src+'" alt="Plaque"/>' if img_src else ''}
    <h1 style="font-weight:900; font-size:2.3rem; margin-bottom:5px;">
        Retrouvez quelle voiture c'était !
    </h1>
    <p style="color:#555; font-size:1.08rem; margin-top:-5px;">
        Entrez une plaque d'immatriculation pour afficher les détails du véhicule
    </p>
</div>
""", unsafe_allow_html=True)


# --- Génération de la plaque ---
TEMPLATE_PATH = Path("Data/images/plaque_vierge.png")
FONT_PATH     = Path("Data/fonts/dejavu-sans-bold.ttf")

#st.write("CWD:", os.getcwd())
#st.write("Font exists:", FONT_PATH.exists())

def generate_plate(text: str):
    # normalisation
    text = text.upper().replace(" ", "")

    # ouvre la plaque vierge
    plate = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(plate)

    # charge police
    try:
        font = ImageFont.truetype(str(FONT_PATH), 130)
    except Exception as e:
        st.warning(f"Police introuvable, fallback utilisé. Erreur : {e}")
        font = ImageFont.load_default()

#    st.write(font.getname())

    # Pillow 10+ : textbbox pour mesurer correctement le texte
    bbox = draw.textbbox((0, 0), text, font=font)  # (x0,y0,x1,y1)
    wtxt = bbox[2] - bbox[0]
    htxt = bbox[3] - bbox[1]

    # dimensions
    W, H = plate.size

    # position centrale (ajuste H * 0.28 si besoin)
    x = (W - wtxt) // 2
    y = int(H * 0.28)

    # texte noir (léger faux gras)
    for dx, dy in [(0,0),(1,0),(0,1),(-1,0),(0,-1)]:
        draw.text((x+dx, y+dy), text, font=font, fill="black")

    return plate


# --- Widgets (à l'extérieur du HTML) ---
plaque = st.text_input("", placeholder="Exemple : AB123CD")
rechercher = st.button("Rechercher")

# 1) Récupération des secret
TOKEN = st.secrets.get("AUTOWAYS_TOKEN")
BASE  = st.secrets.get("AUTOWAYS_BASE", "https://app.auto-ways.net/api/v1/fr")

# 2) Assert simple pour éviter de chercher si pas token oublié
if not TOKEN:
    st.error("TOKEN manquant : configure AUTOWAYS_TOKEN dans .streamlit/secrets.toml ou en variable d'environnement.")
    st.stop()

# Fonction pour récupérer les données du modèle
def get_modele(plaque):
#   url = f"https://app.auto-ways.net/api/v1/fr?token={API_KEY}&plaque={plaque}"

    # Si aucun token → retourne une fausse réponse locale
    if TEST_MODE:
        return {
            "data": {
                "AWN_marque": "PORSCHE",
                "AWN_label": "BOXSTER 2.7",
                "AWN_date_mise_en_circulation": "2007-05-09",
                "AWN_energie": "ESSENCE",
                "AWN_puissance_chevaux": 245,
                "AWN_couleur": "BLEU",
                "AWN_style_carrosserie": "CABRIOLET",
                "AWN_marque_image": None,
                "AWN_model_image": None
            }
        }

    # Sinon → vrai appel API
    url = f"{BASE}?token={TOKEN}&plaque={plaque}"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
# Bouton pour lancer la recherche
if rechercher:
    img = generate_plate(plaque)
    st.image(img)

    payload = get_modele(plaque)
    data = payload.get('data', {}) # le sous-dictionnaire 'data' contient les champs AWN avec les informations du véhicule

   # Récupération sûre (évite les KeyError)
    marque = data.get("AWN_marque")
    logo_marque = data.get("AWN_marque_image")
    modele = data.get("AWN_label")
    logo_modele = data.get("AWN_model_image")
    date_mise_en_circulation = data.get("AWN_date_mise_en_circulation")
    energie = data.get("AWN_energie")
    cylindree_liters = data.get("AWN_cylindree_liters")
    puissance_chevaux = data.get("AWN_puissance_chevaux")
    max_speed = data.get("AWN_max_speed")
    couleur = data.get("AWN_couleur")
    style_carrosserie = data.get("AWN_style_carrosserie")
    nbr_places = data.get("AWN_nbr_places")

    if data:
        st.subheader("Informations du véhicule")

        col_logo, col_info = st.columns([1, 3])  # Colonne pour le logo et colonne pour les infos
        with col_logo:
            if logo_marque:
                st.image(logo_marque, width=100)  # Affiche le logo de la marque
            else:
                st.write("Logo de la marque non disponible")
        with col_info:
            if marque:
                st.markdown(f"**Marque :** 🏷️ {marque}")
            if modele:
                st.markdown(f"**Modèle :** {modele}")
            if date_mise_en_circulation:
                st.markdown(f"**Date de mise en circulation :** {date_mise_en_circulation}")
            if energie:
                st.markdown(f"**Type de carburant :** {energie}")
            if cylindree_liters:
                st.markdown(f"**Volume du moteur (en litres) :** {cylindree_liters}")
            if puissance_chevaux:
                st.markdown(f"**Puissance réelle (en chevaux) :** {puissance_chevaux}") 
            if max_speed:
                st.markdown(f"**Vitesse maximale (en km/h) :** {max_speed}")
            if couleur:
                st.markdown(f"**Couleur :** {couleur}")
            if style_carrosserie:
                st.markdown(f"**Type de véhicule :** {style_carrosserie}")
            if nbr_places:
                st.markdown(f"**Nombre de places :** {nbr_places}")
        
#        st.markdown("---")  # Séparateur visuel
        st.divider()
        if logo_modele:
            st.image(logo_modele, width=200)  # Affiche l'image du véhicule

    else:
        st.write("Aucune donnée trouvée pour cette plaque.")
