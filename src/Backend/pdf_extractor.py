# import fitz  # PyMuPDF
# from PIL import Image
# import pytesseract
# import uuid
# import re
# f            # Cleaning non-breaking spaces and converting bullet characters to standard bullet
#             content = content.replace('\u2022', '•').replace('\uf0b7', '•')
#             # Handling lists
#             if '•' in content:
#                 items = [itm.strip(' ;:') for itm in content.split('•') if itm.strip()]
#                 html_output.append("<ul>")
#                 for itm in items:
#                     html_output.append(f"<li>{itm}</li>")
#                 html_output.append("</ul>")port BytesIO
# import camelot

# pdf_path = input("Entrez le chemin du fichier PDF : ")
# if not pdf_path.endswith('.pdf'):
#     print("Le fichier doit être un PDF.")
#     exit(1)

# doc = fitz.open(pdf_path)

# # HTML header
# title = fitz.Document(pdf_path).metadata.get('title', 'Document')
# html_output = [
#     f'<html lang="fr"><head><meta charset="UTF-8"><title>{title} Accessible</title></head><body>'
# ]

# # Funtion to know if a block is a title
# def is_title(block):
#     if block['type'] != 0 or len(block['lines']) == 0:
#         return False
#     max_font = max(
#         span['size']
#         for line in block['lines']
#         for span in line['spans']
#     )
#     return max_font >= max(
#         span['size']
#         for p in doc
#         for b in p.get_text("dict")["blocks"] if b['type']==0
#         for l in b['lines']
#         for span in l['spans']
#     )  # return the max font size of the document therefore we consider it as a title

# # Threshold for column detection
# COL_THRESHOLD = 5

# for page_num, page in enumerate(doc, start=1):
#     html_output.append(f"<section aria-label='Page {page_num}'>")
#     # 1) Table extraction with Camelot
#     tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
#     if tables:
#         for t in tables:
#             df = t.df.copy()
#             # First row as header
#             df.columns = df.iloc[0]
#             df = df.drop(0).reset_index(drop=True)
#             html_output.append("<table role='table'>")
#             html_output.append("<thead><tr>")
#             for col in df.columns:
#                 html_output.append(f"<th scope='col'>{col}</th>")
#             html_output.append("</tr></thead><tbody>")
            
#             for _, row in df.iterrows():
#                 html_output.append("<tr>")
#                 for cell in row:
#                     html_output.append(f"<td>{cell}</td>")
#                 html_output.append("</tr>")
#             html_output.append("</tbody></table>")
#         html_output.append("</section>")
#         continue  # Iterate to each page

#     # 2) If there are no tables, we extract the text
#     blocks = sorted(
#         page.get_text("dict")["blocks"],
#         key=lambda b: (b.get("bbox", [0,0,0,0])[1], b.get("bbox", [0,0,0,0])[0])
#     )
#     for block in blocks:
#         if block["type"] == 0:
#             # Placing the text in the right order
#             raw_lines = []
#             for line in block["lines"]:
#                 spans = [
#                     (span["bbox"][0], span["text"])
#                     for span in line["spans"]
#                     if span["text"].strip()
#                 ]
#                 if spans:
#                     raw_lines.append(spans)
#             # Joining the lines 
#             content = " ".join(
#                 span["text"].strip()
#                 for line in block["lines"]
#                 for span in line["spans"]
#                 if span["text"].strip()
#             )
#             if not content:
#                 continue
#             # Cleaning non-breaking spaces and other characters
#             content = content.replace('\u2022', '').replace('\uf0b7', '')
#             # Handling lists
#             if '' in content:
#                 items = [itm.strip(' ;:') for itm in content.split('') if itm.strip()]
#                 html_output.append("<ul>")
#                 for itm in items:
#                     html_output.append(f"<li>{itm}</li>")
#                 html_output.append("</ul>")
#                 continue
#             # Handling paragraphs and titles
#             tag = "h2" if is_title(block) else "p"
#             html_output.append(f"<{tag}>{content}</{tag}>")
#         elif block["type"] == 1:
#             # Handling images
#             raw = block.get("image")
#             if not raw:
#                 continue
#             pil_img = Image.open(BytesIO(raw))
#             ext = 'jpg' if pil_img.format.lower() == 'jpeg' else pil_img.format.lower()
#             img_fn = f"image_{page_num}_{uuid.uuid4().hex}.{ext}"
#             pil_img.save(img_fn)
#             alt = pytesseract.image_to_string(pil_img, lang="fra").strip() or "Image sans description détectable"
#             html_output.append(
#                 "<figure>"
#                 f"<img src='{img_fn}' alt='{alt}'>"
#                 f"<figcaption>{alt}</figcaption>"
#                 "</figure>"
#             )
#     html_output.append("</section>")

# html_output.append("</body></html>")

# # Save the HTML output to a file
# out_path = pdf_path.replace('.pdf', ' Accessible.html')
# with open(out_path, 'w', encoding='utf-8') as f:
#     f.write("\n".join(html_output))

# print("Fichier généré :", out_path)
# print("Extraction terminée.")
# # 