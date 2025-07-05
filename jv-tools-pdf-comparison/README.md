# PDF Checker - PDF Comparison Tool

A web-based PDF comparison tool that allows users to upload two PDF files and view their differences with highlighted changes.

## Features

- **PDF Upload**: Upload two PDF files for comparison
- **Text Extraction**: Extracts text content from PDFs using pdfplumber
- **Difference Highlighting**: Shows added text in green and removed text in red
- **Paragraph-by-Paragraph Comparison**: Displays differences organized by paragraphs
- **Clean Interface**: Modern, responsive design using Bootstrap

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd jv-tools-pdf-comparison
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python3 app.py
   ```

4. **Access the tool**:
   Open your browser and go to `http://127.0.0.1:5000/`

## Usage

1. **Upload PDFs**: Select two PDF files to compare
2. **Compare**: Click "Compare PDFs" to process the files
3. **View Results**: See the differences highlighted in the comparison table
4. **Repeat**: Use "Compare Another" to start a new comparison

## Project Structure

```
jv-tools-pdf-comparison/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── index.html        # Upload page
│   └── result.html       # Results page
├── uploads/              # Temporary storage for uploaded PDFs
└── README.md            # This file
```

## Technologies Used

- **Backend**: Flask (Python)
- **PDF Processing**: pdfplumber
- **Text Comparison**: difflib
- **Frontend**: Bootstrap 5
- **File Handling**: Werkzeug

## Development

The application runs in debug mode by default. For production deployment, consider using a WSGI server like Gunicorn.

## License

This project is open source and available under the MIT License.