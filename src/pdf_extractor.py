import fitz  # PyMuPDF
import os

def extract_pdf_details(pdf_path):
    doc = fitz.open(pdf_path)

    metadata = doc.metadata

    full_text = []
    fonts = set()
    font_sizes = set()
    links = []
    images = []
    structured_lines = []

    # --- Collect link info ---
    link_map = {}
    for page_num, page in enumerate(doc):
        link_map[page_num] = []
        for link in page.get_links():
            if "uri" in link:
                links.append({
                    "uri": link["uri"],
                    "page": page_num + 1,
                    "rect": link["from"]
                })
                link_map[page_num].append((link["from"], link["uri"]))

    all_font_sizes = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    fonts_in_line = []
                    sizes_in_line = []
                    colors_in_line = []
                    span_positions = []

                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue

                        font = span["font"]
                        size = span["size"]
                        bbox = span["bbox"]
                        color_int = span.get("color", 0)

                        # Make sure small font sizes are readable
                        if size < 9:
                            size = 12

                        # Color conversion from int to rgb
                        r = (color_int >> 16) & 255
                        g = (color_int >> 8) & 255
                        b = color_int & 255
                        hex_color = f"rgb({r}, {g}, {b})"

                        fonts.add(font)
                        font_sizes.add(size)
                        all_font_sizes.append(size)

                        # Detect hyperlink
                        link_uri = None
                        for link_rect, uri in link_map.get(page_num, []):
                            if fitz.Rect(link_rect).intersects(fitz.Rect(bbox)):
                                link_uri = uri
                                break

                        if link_uri:
                            text = f'<a href="{link_uri}">{text}</a>'

                        fonts_in_line.append(font)
                        sizes_in_line.append(size)
                        colors_in_line.append(hex_color)
                        span_positions.append(bbox)
                        line_text += text + " "

                    if line_text:
                        avg_size = sum(sizes_in_line) / len(sizes_in_line)
                        avg_color = colors_in_line[0] if colors_in_line else "#000000"
                        main_font = max(set(fonts_in_line), key=fonts_in_line.count)
                        is_bold = "Bold" in main_font
                        is_italic = "Italic" in main_font or "Oblique" in main_font
                        tag = "h1" if avg_size >= max(all_font_sizes) - 1 else "p"

                        structured_lines.append({
                            "tag": tag,
                            "text": line_text.strip(),
                            "font": main_font,
                            "size": round(avg_size, 1),
                            "color": avg_color,
                            "bbox": span_positions[0],
                            "page": page_num + 1,
                            "bold": is_bold,
                            "italic": is_italic
                        })

                        full_text.append(line_text.strip())

    # --- Extract Images ---
    for page_num, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append({
                "page": page_num + 1,
                "xref": xref,
                "format": base_image["ext"],
                "width": base_image["width"],
                "height": base_image["height"]
            })

    # --- Build HTML ---
    html_lines = []
    for line in structured_lines:
        style = f"font-size:{line['size']}pt; font-family:{line['font']}; color:{line['color']};"
        if line["bold"]:
            style += " font-weight: bold;"
        if line["italic"]:
            style += " font-style: italic;"
        html_lines.append(f'<{line["tag"]} style="{style}">{line["text"]}</{line["tag"]}>')

    return {
        "metadata": metadata,
        "text": "\n".join(full_text),
        "fonts": list(fonts),
        "font_sizes": sorted(list(font_sizes)),
        "links": links,
        "images": images,
        "html_text": "\n".join(html_lines),
        "structured_text": structured_lines
    }

print(extract_pdf_details("data/Exemple court de document non conforme 3.pdf"))

