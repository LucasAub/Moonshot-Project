#!/usr/bin/env python3

import os
import argparse
from pdf_extractor import extract_structure
from images_analyzer import generate_alt_text
from html_builder import HTML_TEMPLATE
import fitz

def detect_tables(pdf_path, page_number):
    """
    Utilise Camelot pour extraire les tableaux d’une page donnée.
    Retourne liste de dict {header: [...], rows: [[...], ...]}.
    """
    import camelot
    tables = []
    camelot_tables = camelot.read_pdf(pdf_path, pages=str(page_number+1))
    for t in camelot_tables:
        df = t.df
        header = df.iloc[0].tolist()
        rows = df.iloc[1:].values.tolist()
        tables.append({"header": header, "rows": rows})
    return tables

def main():
    parser = argparse.ArgumentParser(
        description="Convertit un PDF en PDF taggé accessible pour screenreaders"
    )
    parser.add_argument("-i","--input",  required=True, help="PDF source")
    parser.add_argument("-o","--output", required=True, help="PDF final accessible")
    parser.add_argument("-m","--method", choices=["prince","borb"], default="prince",
                        help="PrinceXML (par défaut) ou borb")
    args = parser.parse_args()

    pages = extract_structure(args.input)
    os.makedirs("images", exist_ok=True)

    # Détection des tableaux et préparation des images
    for page in pages:
        page["tables"] = detect_tables(args.input, page["spans"][0]["page"])
        imgs_out = []
        for img in page["images"]:
            fn = f"images/page{img['page']}_img{img['xref']}.png"
            img["pix"].save(fn)
            alt = generate_alt_text(fn)
            imgs_out.append({"path": fn, "alt": alt})
        page["images"] = imgs_out

    # Génération du HTML intermédiaire
    from jinja2 import Template
    html = Template(HTML_TEMPLATE).render(pages=pages)
    with open("document.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("→ document.html créé")

    # Conversion finale
    if args.method == "prince":
        cmd = f"prince --accessibility document.html -o {args.output}"
        print("Exécution :", cmd)
        os.system(cmd)
    else:
        # ==== BRANCHE borb ====
        from borb.pdf.document import Document
        from borb.pdf.page.page import Page
        from borb.pdf.pdf import PDF
        from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
        from borb.pdf.canvas.layout.text.paragraph import Paragraph
        from borb.pdf.canvas.layout.image.image import Image

        doc = Document()
        for page in pages:
            # Au lieu de append_page(), on crée une Page et on l'ajoute
            p = Page()                           
            doc.add_page(p)                     # :contentReference[oaicite:0]{index=0}
            layout = SingleColumnLayout(p)

            for span in page["spans"]:
                layout.add(
                    Paragraph(span["text"])
                    .set_tag(span["tag"].upper())
                )

            for table in page["tables"]:
                # TODO : conversion Table → Flowable borb si nécessaire
                pass

            for img in page["images"]:
                layout.add(
                    Image(img["path"])
                    .set_alt_text(img["alt"])
                )

        with open(args.output, "wb") as out:
            PDF.dumps(out, doc)

        print(f"→ {args.output} créé avec borb")

if __name__ == "__main__":
    main()
