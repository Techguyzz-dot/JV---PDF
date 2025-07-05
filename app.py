from flask import Flask, request, render_template, redirect, url_for
import pdfplumber
import difflib
from html import escape
import os
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Use temporary directory for file uploads in serverless environment
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Utility Functions
def extract_paragraphs(pdf_path):
    paragraphs = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts = [p.strip() for p in text.split('\n\n') if p.strip()]
                    paragraphs.extend(parts)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []
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
        try:
            pdf1 = request.files['pdf1']
            pdf2 = request.files['pdf2']
            if not pdf1 or not pdf2:
                return "Please upload both PDF files."
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp1:
                pdf1.save(tmp1.name)
                pdf1_path = tmp1.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp2:
                pdf2.save(tmp2.name)
                pdf2_path = tmp2.name
            
            paras1 = extract_paragraphs(pdf1_path)
            paras2 = extract_paragraphs(pdf2_path)
            paras1, paras2 = pad_lists(paras1, paras2)
            
            comparison = []
            for idx, (p1, p2) in enumerate(zip(paras1, paras2), 1):
                highlighted_p1 = get_inline_diff(p1, p2, mode='pdf1')
                highlighted_p2 = get_inline_diff(p1, p2, mode='pdf2')
                comparison.append((f"Paragraph {idx}", highlighted_p1, highlighted_p2))
            
            # Clean up temporary files
            try:
                os.unlink(pdf1_path)
                os.unlink(pdf2_path)
            except:
                pass
                
            return render_template('result.html', comparison=comparison)
        except Exception as e:
            return f"Error processing PDFs: {str(e)}"
    
    return render_template('index.html')

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=True, port=8000) 