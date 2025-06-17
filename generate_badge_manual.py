import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

# === Chemins ===
badge_template_path = "badge_template.png"
font_path = "Lato-Bold.ttf"  # police Lato Bold
output_path = "generated_badge.png"

# === Données utilisateur ===
first_name = "Joffre"
last_name = "Niyondiko"
registration_number = "JEAABC"
statut = "Universite Polytechnique De Gitega"
qr_data = f"https://example.com/registration/{registration_number}"

# === Vérification modèle ===
if not os.path.exists(badge_template_path):
    raise FileNotFoundError(f"Modèle introuvable : {badge_template_path}")

# === Charger l'image sans agrandissement au début ===
badge_img = Image.open(badge_template_path).convert("RGBA")
badge_width, badge_height = badge_img.size
max_width = badge_width * 0.9

draw = ImageDraw.Draw(badge_img)

# === QR Code ===
qr = qrcode.QRCode(version=1, box_size=15, border=5)
qr.add_data(qr_data)
qr.make(fit=True)
qr_img = qr.make_image(fill="black", back_color="white")

# === Facteur d'agrandissement ===
scale_factor = 1.5

# Taille QR code initiale puis ajustée selon scale_factor
qr_size = (650, 650)
qr_size_scaled = (int(qr_size[0] * scale_factor), int(qr_size[1] * scale_factor))
qr_img = qr_img.resize(qr_size_scaled, Image.Resampling.BICUBIC)

# === Position QR Code ===
qr_x = badge_width // 2 - qr_size_scaled[0] // 2
qr_y = 3350
badge_img.paste(qr_img, (qr_x, qr_y))

# === NOM COMPLET ===
full_name = f"{last_name.upper()} {first_name}"
name_font_size = 250
while True:
    try:
        font_name = ImageFont.truetype(font_path, size=name_font_size)
    except:
        font_name = ImageFont.load_default()
    name_bbox = draw.textbbox((0, 0), full_name, font=font_name)
    name_width = name_bbox[2] - name_bbox[0]
    if name_width <= max_width or name_font_size <= 100:
        break
    name_font_size -= 5

name_x = badge_width // 2 - name_width // 2
name_y = 2850
draw.text((name_x, name_y), full_name, fill="white", font=font_name)

# === STATUT PART 1 (ex : ENTREPRISE) ===
statut_part1 = "ENTREPRISE"
statut_font_size = 280
letter_spacing = 30
letters = list(statut_part1)

while True:
    try:
        font_statut = ImageFont.truetype(font_path, size=statut_font_size)
    except:
        font_statut = ImageFont.load_default()
    total_width = 0
    letter_positions = []
    for letter in letters:
        bbox = draw.textbbox((0, 0), letter, font=font_statut)
        letter_width = bbox[2] - bbox[0]
        letter_positions.append((letter, total_width))
        total_width += letter_width + letter_spacing
    if total_width <= max_width or statut_font_size <= 150:
        break
    statut_font_size -= 5

start_x = badge_width // 2 - total_width // 2
y_statut1 = 4500
for letter, offset in letter_positions:
    draw.text((start_x + offset, y_statut1), letter, fill="white", font=font_statut)

# === STATUT PART 2 ===
statut_part2 = statut
societe_font_size = 100
while True:
    try:
        font_societe = ImageFont.truetype(font_path, size=societe_font_size)
    except:
        font_societe = ImageFont.load_default()
    statut_bbox2 = draw.textbbox((0, 0), statut_part2, font=font_societe)
    statut_width2 = statut_bbox2[2] - statut_bbox2[0]
    if statut_width2 <= max_width or societe_font_size <= 60:
        break
    societe_font_size -= 5

statut_x = badge_width // 2 - statut_width2 // 2
statut_y = 4900
draw.text((statut_x, statut_y), statut_part2, fill="white", font=font_societe)

# === Agrandir tout le badge à la fin ===
new_width = int(badge_img.width * scale_factor)
new_height = int(badge_img.height * scale_factor)
badge_img = badge_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

# === Sauvegarde ===
badge_img.save(output_path, format="PNG", dpi=(300, 300))
print(f"✅ Badge généré avec succès : {output_path}")
