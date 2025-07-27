from flask import Flask, request, render_template, redirect, url_for, jsonify
import pdfplumber
import difflib
from html import escape
import os
import tempfile
import json
from werkzeug.utils import secure_filename
from docx import Document
import hashlib
import uuid

app = Flask(__name__)

# Use temporary directory for file uploads in serverless environment
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# In-memory storage for comparison results (in production, use Redis or database)
comparison_results = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_hash(file_path):
    """Calculate MD5 hash of file content"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_text_from_word(docx_path):
    """Extract text from Word document"""
    try:
        doc = Document(docx_path)
        paragraphs = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraphs.append(text)
        return paragraphs
    except Exception as e:
        print(f"Error extracting text from Word document: {e}")
        return []

def extract_paragraphs(file_path, file_extension):
    """Extract paragraphs from PDF or Word document"""
    if file_extension.lower() == 'pdf':
        paragraphs = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        parts = [p.strip() for p in text.split('\n\n') if p.strip()]
                        paragraphs.extend(parts)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return []
        return paragraphs
    elif file_extension.lower() in ['docx', 'doc']:
        return extract_text_from_word(file_path)
    else:
        return []

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
        if word.startswith('- ') and mode == 'file1':
            result.append(f'<span class="removed">{escape(word[2:])}</span>')
        elif word.startswith('+ ') and mode == 'file2':
            result.append(f'<span class="added">{escape(word[2:])}</span>')
        elif word.startswith(' '):
            result.append(escape(word[2:]))
    return ' '.join(result)

def calculate_similarity(text1, text2):
    """Calculate similarity percentage between two texts"""
    if not text1 and not text2:
        return 100.0
    if not text1 or not text2:
        return 0.0
    
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    return round(similarity * 100, 2)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            file1 = request.files['file1']
            file2 = request.files['file2']
            
            if not file1 or not file2:
                return jsonify({'error': 'Please upload both files.'}), 400
            
            if not allowed_file(file1.filename) or not allowed_file(file2.filename):
                return jsonify({'error': 'Please upload only PDF or Word documents.'}), 400
            
            # Get file extensions
            ext1 = file1.filename.rsplit('.', 1)[1].lower() if file1.filename else 'pdf'
            ext2 = file2.filename.rsplit('.', 1)[1].lower() if file2.filename else 'pdf'
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext1}') as tmp1:
                file1.save(tmp1.name)
                file1_path = tmp1.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext2}') as tmp2:
                file2.save(tmp2.name)
                file2_path = tmp2.name
            
            # Check if files are identical
            hash1 = get_file_hash(file1_path)
            hash2 = get_file_hash(file2_path)
            
            if hash1 == hash2:
                # Clean up temporary files
                try:
                    os.unlink(file1_path)
                    os.unlink(file2_path)
                except:
                    pass
                
                return jsonify({
                    'identical': True,
                    'message': 'No differences found - Files are identical!',
                    'similarity': 100.0
                })
            
            # Extract text from both files
            paras1 = extract_paragraphs(file1_path, ext1)
            paras2 = extract_paragraphs(file2_path, ext2)
            
            if not paras1 and not paras2:
                return jsonify({'error': 'Could not extract text from the uploaded files.'}), 400
            
            paras1, paras2 = pad_lists(paras1, paras2)
            
            # Calculate overall similarity
            combined_text1 = ' '.join(paras1)
            combined_text2 = ' '.join(paras2)
            similarity = calculate_similarity(combined_text1, combined_text2)
            
            comparison = []
            differences_found = False
            
            for idx, (p1, p2) in enumerate(zip(paras1, paras2), 1):
                highlighted_p1 = get_inline_diff(p1, p2, mode='file1')
                highlighted_p2 = get_inline_diff(p1, p2, mode='file2')
                
                # Check if this paragraph has differences
                if p1 != p2:
                    differences_found = True
                
                comparison.append((f"Paragraph {idx}", highlighted_p1, highlighted_p2))
            
            # Clean up temporary files
            try:
                os.unlink(file1_path)
                os.unlink(file2_path)
            except:
                pass
            
            # If no differences found in content
            if not differences_found and similarity > 95:
                return jsonify({
                    'identical': True,
                    'message': 'No differences found - Content is identical!',
                    'similarity': similarity
                })
            
            # Generate unique ID for this comparison
            comparison_id = str(uuid.uuid4())
            
            # Store data in memory instead of session
            comparison_results[comparison_id] = {
                'identical': False,
                'comparison': comparison,
                'similarity': similarity,
                'file1_name': file1.filename,
                'file2_name': file2.filename,
                'file1_type': ext1.upper(),
                'file2_type': ext2.upper()
            }
            
            return jsonify({
                'redirect': f'/result?id={comparison_id}'
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing files: {str(e)}'}), 500
    
    return render_template('index.html')

@app.route('/result')
def result():
    """Display comparison results"""
    comparison_id = request.args.get('id')
    if not comparison_id or comparison_id not in comparison_results:
        return redirect('/')
    
    data = comparison_results[comparison_id]
    return render_template('result.html', 
                         comparison=data.get('comparison', []),
                         similarity=data.get('similarity', 0),
                         file1_name=data.get('file1_name', ''),
                         file2_name=data.get('file2_name', ''),
                         file1_type=data.get('file1_type', ''),
                         file2_type=data.get('file2_type', ''))

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=True, port=8000)

# Export the Flask app for Vercel
application = app 