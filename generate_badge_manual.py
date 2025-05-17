import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

# Chemins pour les fichiers (adaptez selon votre système)
badge_template_path = "badge_template.png"  # Remplacez par le chemin de votre modèle
font_path = "arialbd.ttf"  # Police Arial Bold (ou remplacez par une police disponible)
output_path = "generated_badge.png"

# Données de l'utilisateur (à personnaliser)
first_name = "Niyondiko"
last_name = "Joffre"
registration_number = "JEAABC"
statut = "Universite Polytechnique De Gitega"  # Options : PARTICULIER, ONG, SOCIETE, UNIVERSITE
qr_data = "https://example.com/registration/JEAABC"  # URL pour le QR code

# Vérifier si le modèle existe
if not os.path.exists(badge_template_path):
    raise FileNotFoundError(f"Le fichier modèle {badge_template_path} n'existe pas.")

# Charger le modèle de badge
badge_img = Image.open(badge_template_path).convert("RGBA")
badge_width, badge_height = badge_img.size

# Définir une largeur maximale acceptable (90% de la largeur du badge)
max_width = badge_width * 0.9

# Générer le QR code
qr = qrcode.QRCode(version=1, box_size=15, border=5)
qr.add_data(qr_data)
qr.make(fit=True)
qr_img = qr.make_image(fill="black", back_color="white")

# Redimensionner et placer le QR code (valeurs fixes)
qr_size = (280, 280)
qr_img = qr_img.resize(qr_size, Image.Resampling.BICUBIC)
qr_position = (
    badge_img.width // 2 - qr_size[0] // 2,
    1080,
)
badge_img.paste(qr_img, qr_position, qr_img)

# Ajouter le nom et prénom
draw = ImageDraw.Draw(badge_img)
try:
    font = ImageFont.truetype(font_path, size=60)
except Exception:
    font = ImageFont.load_default()

full_name = f"{last_name.upper()} {first_name}"
text_bbox = draw.textbbox((0, 0), full_name, font=font)
text_width = text_bbox[2] - text_bbox[0]

# Ajuster la taille du nom si trop large
name_font_size = 60
while text_width > max_width and name_font_size > 10:
    name_font_size -= 5
    try:
        font = ImageFont.truetype(font_path, size=name_font_size)
    except Exception:
        font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), full_name, font=font)
    text_width = text_bbox[2] - text_bbox[0]

text_position = (
    badge_img.width // 2 - text_width // 2,
    850,
)
draw.text(text_position, full_name, fill="white", font=font)

# Ajouter le statut (séparé en deux lignes avec une police bold)
statut_font_size = 140
try:
    font_statut = ImageFont.truetype(font_path, size=statut_font_size)
except Exception:
    font_statut = ImageFont.load_default()

try:
    font_societe = ImageFont.truetype(font_path, size=40)
except Exception:
    font_societe = ImageFont.load_default()

# Première ligne : statut_part1 (par exemple, "ENTREPRISE") avec espacement manuel
statut_part1 = "ENTREPRISE"
letter_spacing = 30
letters = list(statut_part1)
total_width = 0
letter_positions = []

# Calculer la largeur totale avec espacement
for letter in letters:
    bbox = draw.textbbox((0, 0), letter, font=font_statut)
    letter_width = bbox[2] - bbox[0]
    letter_positions.append((letter, total_width))
    total_width += letter_width + letter_spacing

# Ajuster la taille de la police si la largeur dépasse
while total_width > max_width and statut_font_size > 20:
    statut_font_size -= 10
    try:
        font_statut = ImageFont.truetype(font_path, size=statut_font_size)
    except Exception:
        font_statut = ImageFont.load_default()
    total_width = 0
    letter_positions = []
    for letter in letters:
        bbox = draw.textbbox((0, 0), letter, font=font_statut)
        letter_width = bbox[2] - bbox[0]
        letter_positions.append((letter, total_width))
        total_width += letter_width + letter_spacing

# Ajuster l'espacement si la largeur est encore trop grande
while total_width > max_width and letter_spacing > 5:
    letter_spacing -= 5
    total_width = 0
    letter_positions = []
    for letter in letters:
        bbox = draw.textbbox((0, 0), letter, font=font_statut)
        letter_width = bbox[2] - bbox[0]
        letter_positions.append((letter, total_width))
        total_width += letter_width + letter_spacing

# Ajuster pour centrer toutes les lettres
start_x = badge_img.width // 2 - total_width // 2
for letter, offset in letter_positions:
    draw.text((start_x + offset, 1450), letter, fill="white", font=font_statut)

# Deuxième ligne : le statut (par exemple, "Universite Polytechnique De Gitega")
societe_font_size = 40
statut_part2 = statut
statut_bbox2 = draw.textbbox((0, 0), statut_part2, font=font_societe)
statut_width2 = statut_bbox2[2] - statut_bbox2[0]

# Ajuster la taille si le statut est trop large
while statut_width2 > max_width and societe_font_size > 10:
    societe_font_size -= 5
    try:
        font_societe = ImageFont.truetype(font_path, size=societe_font_size)
    except Exception:
        font_societe = ImageFont.load_default()
    statut_bbox2 = draw.textbbox((0, 0), statut_part2, font=font_societe)
    statut_width2 = statut_bbox2[2] - statut_bbox2[0]

statut_position2 = (
    badge_img.width // 2 - statut_width2 // 2,
    1650,
)
draw.text(statut_position2, statut_part2, fill="white", font=font_societe)

# Sauvegarder l'image générée avec très haute qualité
badge_img.save(output_path, format="PNG", quality=100, dpi=(300, 300))
print(f"Badge généré avec succès : {output_path}")
