from flask import Flask, request, jsonify
import fitz
import spacy
import textacy
from sentence_transformers import SentenceTransformer, util
import mysql.connector
import os
import re
import json

app = Flask(__name__)

#for file validation
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
UPLOAD_DIRECTORY = "./data/resumes/"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_DIRECTORY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

#to load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')

#to initialize SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_filename(filename):
    return re.match(r'^[\w\-. ]+$', filename) is not None


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_key_terms(text):
    doc = nlp(text)
    key_terms = textacy.extract.keyterms.textrank(doc, normalize="lemma", topn=50)
    return [term for term, _ in key_terms]


def calculate_similarity(text1, text2):
    embed1 = model.encode(text1, convert_to_tensor=True)
    embed2 = model.encode(text2, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embed1, embed2)
    return similarity.item()


def get_job_description_path(category):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='cv-matcher'
        )
        cursor = conn.cursor()
        query = "SELECT path FROM files WHERE category = %s"
        cursor.execute(query, (category,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0]
        else:
            return None
    except mysql.connector.Error as err:
        return None


def initialize_static_id():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='cv-matcher'
        )
        cursor = conn.cursor()
        query = "SELECT MAX(id) FROM similarities"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result[0] is not None:
            return result[0] + 1
        else:
            return 1
    except mysql.connector.Error as err:
        return None

id = initialize_static_id()

def insert_similarity_data(name, category, similarity_score, resume_terms, job_desc_terms):
    global id
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='cv-matcher'
        )
        cursor = conn.cursor()
        query = ("INSERT INTO similarities (id, name, category, similarity_score, resume_terms, job_desc_terms) VALUES "
                 "(%s, %s, %s, %s, %s, %s)")
        cursor.execute(query, (id, name, category, similarity_score, json.dumps(resume_terms), json.dumps(job_desc_terms)))
        conn.commit()
        cursor.close()
        conn.close()
        id += 1
    except mysql.connector.Error as err:
        pass

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    if not validate_filename(file.filename):
        return jsonify({"error": "Invalid file name"}), 400

    category = request.form['category']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    job_desc_pdf_path = get_job_description_path(category)
    if not job_desc_pdf_path:
        return jsonify({"error": "Job description not found"}), 404

    resume_text = extract_text_from_pdf(file_path)
    job_desc_text = extract_text_from_pdf(job_desc_pdf_path.decode('utf-8'))

    #to sanitize content: check if the PDF content is valid text
    if not resume_text.strip():
        return jsonify({"error": "Uploaded file content is empty or invalid"}), 400

    resume_terms = extract_key_terms(resume_text)
    job_desc_terms = extract_key_terms(job_desc_text)
    resume_terms_text = ' '.join(resume_terms)
    job_desc_terms_text = ' '.join(job_desc_terms)
    similarity = calculate_similarity(resume_terms_text, job_desc_terms_text)

    insert_similarity_data(file.filename, category, similarity, resume_terms, job_desc_terms)

    return jsonify({
        "similarity_score": similarity,
        "resume_terms": resume_terms,
        "job_desc_terms": job_desc_terms
    })


@app.route('/')
def index():
    return "Welcome to the Resume Matching Service!"


if __name__ == '__main__':
    app.run(debug=True)
