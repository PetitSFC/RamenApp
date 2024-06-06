import streamlit as st
import io
import pdfkit
import tempfile
import os
import fitz  # PyMuPDF
from typing_extensions import Required

# Funktion zum Ersetzen von Variablen in der HTML-Vorlage
def replace_text_in_html(template_html, replacements):
    for key, value in replacements.items():
        template_html = template_html.replace(key, value)
    return template_html

# Funktion zum Konvertieren von HTML zu PDF im "headless" Modus
def convert_html_to_pdf(html_content, header_html, footer_html):
    options = {
        'no-images': '',
        'disable-javascript': '',
        'enable-local-file-access': '',  # Erlaube den Zugriff auf lokale Dateien
        'quiet': '',
        'header-html': header_html,
        'footer-html': footer_html,
        'margin-top': '40mm',  # Erhöhter Platz für die Kopfzeile
        'margin-bottom': '40mm',  # Erhöhter Platz für die Fußzeile
        'footer-right': '[page]',  # Nur die Seitenzahl
        'footer-font-size': '10',  # Schriftgröße der Seitenzahlen
        'footer-spacing': '5'  # Abstand der Seitenzahlen
    }
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_html:
            temp_html.write(html_content.encode('utf-8'))
            temp_html.close()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                pdfkit.from_file(temp_html.name, temp_pdf.name, options=options)
                with open(temp_pdf.name, "rb") as f:
                    pdf_content = f.read()
        return pdf_content, temp_pdf.name
    except IOError as e:
        st.error(f"IOError: {e}")
    except OSError as e:
        st.error(f"OSError: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    finally:
        os.remove(temp_html.name)

# Funktion zum Hinzufügen der Unterschrift und des Stempels zur PDF
def add_images_to_pdf(pdf_path, signature_path, stamp_path, output_path, sig_x, sig_y, sig_width, sig_height, stamp_x, stamp_y, stamp_width, stamp_height):
    try:
        doc = fitz.open(pdf_path)
        page = doc[-1]  # Letzte Seite

        # Dynamische Positionierung der Unterschrift und des Stempels
        text_instances = page.search_for("Unterschrift")
        if text_instances:
            # Positioniere die Bilder relativ zur ersten Instanz des Textes "Unterschrift"
            text_rect = text_instances[0]
            stamp_y = text_rect.y0 - stamp_height + 20  # 20 Pixel Abstand unter dem Text
            sig_y = text_rect.y0 - sig_height - 20  # 20 Pixel Abstand über dem Text

            # Stempel hinzufügen
            stamp_rect = fitz.Rect(stamp_x, stamp_y, stamp_x + stamp_width, stamp_y + stamp_height)
            page.insert_image(stamp_rect, filename=stamp_path)

            # Unterschrift hinzufügen
            sig_rect = fitz.Rect(sig_x, sig_y, sig_x + sig_width, sig_y + sig_height)
            page.insert_image(sig_rect, filename=signature_path)

        doc.save(output_path)
        doc.close()
        with open(output_path, "rb") as f:
            pdf_content = f.read()
        return pdf_content
    except Exception as e:
        st.error(f"Unexpected error while adding images: {e}")

# Streamlit App
st.set_page_config(page_title="Ramen", page_icon="🍜", layout="centered")

# Einbetten des CSS für die Schriftart
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Grape+Nuts&family=Kablammo&family=Noto+Emoji:wght@300..700&display=swap');
        .kablammo {
            font-family: "Kablammo", system-ui;
            font-optical-sizing: auto;
            font-weight: 400;
            font-style: normal;
            font-variation-settings: "MORF" 0;
        }
        .noto-emoji {
            font-family: "Noto Emoji", sans-serif;
            font-optical-sizing: auto;
            font-weight: 400;
            font-style: normal;
        }
        .grape-nuts-regular {
            font-family: "Grape Nuts", cursive;
            font-weight: 400;
            font-style: normal;
        }
        .small-emoji {
            font-size: 0.8em;  /* Verkleinert das Emoji */
        }
        .stTextInput > div > input {
            font-family: "Kablammo", system-ui;
        }
    </style>
""", unsafe_allow_html=True)

# Anwenden der Schriftart auf den Titel
st.markdown("<h1 class='kablammo'>Ramen <span class='noto-emoji small-emoji'>🍜</span></h1>", unsafe_allow_html=True)

# Passwortschutz
PASSWORD = "Schwertfels123"

if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False

def check_password():
    if st.session_state["password"] == PASSWORD:
        st.session_state.password_correct = True
    else:
        st.error("Falsches Passwort")

if not st.session_state.password_correct:
    st.text_input("Passwort", type="password", on_change=check_password, key="password")
    st.stop()

# Lade die HTML-Vorlage aus dem Projektverzeichnis
template_path = "template.html"
header_path = "header.html"
footer_path = "footer.html"
signatures_path = "signatures.html"
signature_image_path = "unterschrift.png"
stamp_image_path = "stempel.png"

# Initialisiere den Session State
if 'firmenname' not in st.session_state:
    st.session_state.firmenname = ""
if 'anschrift' not in st.session_state:
    st.session_state.anschrift = ""
if 'prozentsatz' not in st.session_state:
    st.session_state.prozentsatz = ""
if 'sondervereinbarung' not in st.session_state:
    st.session_state.sondervereinbarung = []
if 'datum' not in st.session_state:
    st.session_state.datum = ""
if 'output_pdf' not in st.session_state:
    st.session_state.output_pdf = None
if 'pdf_filename' not in st.session_state:
    st.session_state.pdf_filename = ""

firmenname = st.text_input("Firmenname", value=st.session_state.firmenname, key="firmenname_input", placeholder="", help="Geben Sie den Firmennamen ein")
anschrift = st.text_input("Anschrift", value=st.session_state.anschrift, key="anschrift_input", placeholder="", help="Geben Sie die Anschrift ein")

# Prozentsatz-Eingabefeld mit festem Prozentzeichen
prozentsatz = st.text_input("Prozentsatz", value=st.session_state.prozentsatz, key="prozentsatz_input", placeholder="", help="Geben Sie den Prozentsatz ein")
if not prozentsatz.endswith("%"):
    prozentsatz += "%"

datum = st.text_input("Datum der Unterschrift", value=st.session_state.datum, key="datum_input", placeholder="DD.MM.YYYY", help="Geben Sie das Datum im Format DD.MM.YYYY ein")

sondervereinbarungen = {
    "Nachbesetzung": "Falls der von Schwertfels Consulting vermittelte Kandidat während der Probezeit aus einem Grund kündigt, den nicht der Klient zu vertreten hat, oder seitens des Klienten eine Kündigung ausgesprochen wird, welche nicht der Klient zu vertreten hat, so bemüht sich Schwertfels Consulting um eine Nachbesetzung. In diesem Fall wird für die Nachbesetzung kein Honorar fällig. Für die Nachbesetzung gibt es keine zeitliche Begrenzung. Der Klient trägt die Darlegungs- und Beweislast, dass nicht er die Kündigung zu vertreten hat.",
    "Rückerstattung bei Nichtantreten": "Bei Nichtantritt des Arbeitsverhältnisses wird dem Klienten 100% des bereits ausbezahlten Honorars rückerstattet.",
    "Bei Rückzahlung": "Falls der von Schwertfels Consulting vermittelte Kandidat während der Probezeit aus einem Grund kündigt, den nicht der Klient zu vertreten hat, oder seitens des Klienten eine Kündigung ausgesprochen wird, welche nicht der Klient zu vertreten hat, so erhält der Klient eine Rückzahlung in Höhe von 50% des bereits ausbezahlten Honorars. Der Klient trägt die Darlegungs- und Beweislast, dass nicht er die Kündigung zu vertreten hat.",
    "Für einzelne Berechnungen (25%)": "Für die erste erfolgreiche Vermittlung beträgt das Honorar 25% vom Jahreszielgehalt des Kandidaten.",
    "Für einzelne Berechnungen (30%)": "Für die erste erfolgreiche Vermittlung beträgt das Honorar 30% vom Jahreszielgehalt des Kandidaten.",
    "Drittel Regelung": "Drittel Regelung: 1. 1/3 bei Vertragsunterschrift\n2. 1/3 beim Antritt des Kandidaten.\n3. 1/3 bei Bestehen der Probezeit.",
    "Auswahl bei Kündigung": "Falls der von Schwertfels Consulting vermittelte Kandidat während der Probezeit aus einem Grund kündigt, den nicht der Klient zu vertreten hat, oder seitens des Klienten eine Kündigung ausgesprochen wird, welche nicht der Klient zu vertreten hat, so erhält der Klient die Möglichkeit zwischen\na) einer kostenfreien Nachbesetzung\noder\nb) einer Rückzahlung in Höhe von 50% des bereits ausbezahlten Honorars.",

    "Selten": "Wenn das Arbeitsverhältnis des Kandidaten vor Arbeitsbeginn oder während der Probezeit endet, hat Schwertfels Consulting die Pflicht, dem Auftraggeber eine Gutschrift auszustellen. Der Wert dieser Gutschrift ist abhängig von Anfang und Dauer des Arbeitsverhältnisses. Kündigung innerhalb der ersten 3 Monate der Probezeit: Der Auftraggeber erhält eine Gutschrift in Höhe von 50 % des Vermittlungshonorars. Kündigung innerhalb der letzten 3 Monate der Probezeit: Der Auftraggeber erhält eine Gutschrift in Höhe von 30 % des Vermittlungshonorars. Eine etwaige Gutschrift wird unabhängig von der Position erstattet. Diese Sondervereinbarung tritt nur in Kraft und das Honorar wird nur zurückerstattet, wenn Schwertfels Consulting die Position nicht innerhalb von 6 Monaten neu besetzt hat."
}

sondervereinbarung = st.multiselect("Sondervereinbarung wählen", list(sondervereinbarungen.keys()), default=st.session_state.sondervereinbarung, help="Wählen Sie eine oder mehrere Sondervereinbarungen aus")

if st.button("PDF generieren"):
    sondervereinbarung_text = "<ul>" + "".join([f"<li>{sondervereinbarungen[sv]}</li>" for sv in sondervereinbarung]) + "</ul>"
    replacements = {
        "[Firmenname]": firmenname,
        "[Anschrift]": anschrift,
        "[Prozentsatz]": prozentsatz,
        "[Datum]": datum,
        "[Sondervereinbarung]": sondervereinbarung_text
    }

    with open(template_path, "r", encoding="utf-8") as template_file:
        template_html = template_file.read()
        output_html = replace_text_in_html(template_html, replacements)

    with open(signatures_path, "r", encoding="utf-8") as signatures_file:
        signatures_html = signatures_file.read()
        signatures_html = replace_text_in_html(signatures_html, replacements)
        output_html += signatures_html

    # Ersetze den relativen Pfad durch den relativen Pfad
    output_html = output_html.replace("unterschrift.png", "unterschrift.png")

    pdf_content, temp_pdf_path = convert_html_to_pdf(output_html, header_path, footer_path)

    # Füge die Unterschrift und den Stempel zur PDF hinzu
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_signed_pdf:
        # Passe die Koordinaten und Größe des Stempels an
        stamp_x, stamp_y, stamp_width, stamp_height = 30, 200, 170, 170  # Beispielkoordinaten für den Stempel
        # Passe die Koordinaten und Größe der Unterschrift an
        sig_x, sig_y, sig_width, sig_height = -20, 260, 280, 70  # Beispielkoordinaten für die Unterschrift
        signed_pdf_content = add_images_to_pdf(temp_pdf_path, signature_image_path, stamp_image_path, temp_signed_pdf.name, sig_x, sig_y, sig_width, sig_height, stamp_x, stamp_y, stamp_width, stamp_height)

    pdf_filename = f"Rahmenvereinbarung_{firmenname}.pdf"
    st.session_state.output_pdf = signed_pdf_content
    st.session_state.pdf_filename = pdf_filename

    # Clear the input fields
    st.session_state.firmenname = ""
    st.session_state.anschrift = ""
    st.session_state.prozentsatz = ""
    st.session_state.datum = ""
    st.session_state.sondervereinbarung = []
    st.experimental_rerun()

# Zeige den Download-Button, wenn die PDF-Datei generiert wurde
if st.session_state.output_pdf:
    st.download_button(
        label="Download PDF",
        data=st.session_state.output_pdf,
        file_name=st.session_state.pdf_filename,
        mime="application/pdf"
    )

# Credits Abschnitt
st.markdown("---")
st.markdown("<p class='grape-nuts-regular'>Ramen by Janis <span class='noto-emoji'>🐐</span></p>", unsafe_allow_html=True)