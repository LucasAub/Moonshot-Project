# html_builder.py

from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Document Accessible</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    .page { page-break-after: always; }
    table { border-collapse: collapse; margin: 10px 0; }
    th, td { border: 1px solid #666; padding: 4px 8px; }
    th { background: #eee; }
  </style>
</head>
<body>
{% for page in pages %}
  <div class="page">
    {% for span in page.spans %}
      <{{ span.tag }}>{{ span.text | e }}</{{ span.tag }}>
    {% endfor %}

    {% for table in page.tables %}
      <table>
        {% if table.header %}
        <thead>
          <tr>{% for h in table.header %}<th>{{ h | e }}</th>{% endfor %}</tr>
        </thead>
        {% endif %}
        <tbody>
          {% for row in table.rows %}
          <tr>{% for cell in row %}<td>{{ cell | e }}</td>{% endfor %}</tr>
          {% endfor %}
        </tbody>
      </table>
    {% endfor %}

    {% for img in page.images %}
      <img src="{{ img.path }}" alt="{{ img.alt | e }}">
    {% endfor %}
  </div>
{% endfor %}
</body>
</html>
"""
