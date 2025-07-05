from flask import Flask, request, render_template, redirect, url_for
import pdfplumber
import difflib
from html import escape
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Utility Functions
def extract_paragraphs(pdf_path):
    paragraphs = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts = [p.strip() for p in text.split('\n\n') if p.strip()]
                paragraphs.extend(parts)
    return paragraphs

def pad_lists(list1, list2):
    max_len = max(len(list1), len(list2))
    while len(list1) < max_len:
        list1.append("")
    while len(list2) < max_len:
        list2.append("")
    return list1, list2

def get_inline_diff(text1, text2, mode):
    diff = difflib.ndiff(text1.split(), text2.split())
    result = []
    for word in diff:
        if word.startswith('- ') and mode == 'pdf1':
            result.append(f'<span class="removed">{escape(word[2:])}</span>')
        elif word.startswith('+ ') and mode == 'pdf2':
            result.append(f'<span class="added">{escape(word[2:])}</span>')
        elif word.startswith(' '):
            result.append(escape(word[2:]))
    return ' '.join(result)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf1 = request.files['pdf1']
        pdf2 = request.files['pdf2']
        if not pdf1 or not pdf2:
            return "Please upload both PDF files."
        pdf1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf1.filename))
        pdf2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf2.filename))
        pdf1.save(pdf1_path)
        pdf2.save(pdf2_path)
        paras1 = extract_paragraphs(pdf1_path)
        paras2 = extract_paragraphs(pdf2_path)
        paras1, paras2 = pad_lists(paras1, paras2)
        comparison = []
        for idx, (p1, p2) in enumerate(zip(paras1, paras2), 1):
            highlighted_p1 = get_inline_diff(p1, p2, mode='pdf1')
            highlighted_p2 = get_inline_diff(p1, p2, mode='pdf2')
            comparison.append((f"Paragraph {idx}", highlighted_p1, highlighted_p2))
        return render_template('result.html', comparison=comparison)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 