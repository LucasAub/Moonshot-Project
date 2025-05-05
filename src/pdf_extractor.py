# pdf_extractor.py

import fitz  # PyMuPDF
from collections import defaultdict

def extract_structure(pdf_path):
    """
    Ouvre le PDF et retourne une liste de pages.  
    Chaque page est un dict avec :
      - spans : liste de {'text', 'size', 'font', 'bbox', 'tag'}
      - images: liste de {'xref', 'bbox', 'pix'}
    """
    doc = fitz.open(pdf_path)
    all_sizes = []
    pages = []

    # 1. Extraction brute
    for pageno, page in enumerate(doc):
        spans = []
        images = []

        txt = page.get_text("dict")
        for block in txt["blocks"]:
            if block["type"] == 0:  # texte
                for line in block["lines"]:
                    for span in line["spans"]:
                        spans.append({
                            "text": span["text"],
                            "size": span["size"],
                            "font": span["font"],
                            "bbox": span["bbox"],
                            "page": pageno
                        })
                        all_sizes.append(span["size"])

        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            images.append({
                "xref": xref,
                "bbox": page.get_image_bbox(img),
                "pix": pix,
                "page": pageno
            })

        pages.append({"spans": spans, "images": images})

    # 2. Détection des niveaux de titres par font-size
    sizes = sorted(set(all_sizes))
    # On prend jusqu’aux 3 plus grandes tailles
    big = sizes[-3:] if len(sizes) >= 3 else sizes

    def tag_for(size):
        if len(big) >= 3 and size >= big[-1]:
            return "h1"
        elif len(big) >= 2 and size >= big[-2]:
            return "h2"
        elif len(big) >= 1 and size >= big[-3 if len(big)>=3 else 0]:
            return "h3"
        else:
            return "p"

    for page in pages:
        for span in page["spans"]:
            span["tag"] = tag_for(span["size"])

    return pages


if __name__ == "__main__":
    import sys, pprint
    data = extract_structure(sys.argv[1])
    pprint.pprint(data)
