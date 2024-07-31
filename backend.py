from flask import Flask, request, jsonify
import fitz
import spacy
import textacy
from sentence_transformers import SentenceTransformer, util
import mysql.connector
import os

app = Flask(__name__)

#to load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    from spacy.cli import download

    download("en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')

#to initialize SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')


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


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    category = request.form['category']

    file_path = f"./uploads/{file.filename}"
    file.save(file_path)

    job_desc_pdf_path = get_job_description_path(category)
    if not job_desc_pdf_path:
        return jsonify({"error": "Job description not found"}), 404

    resume_text = extract_text_from_pdf(file_path)
    job_desc_text = extract_text_from_pdf(job_desc_pdf_path)
    resume_terms = extract_key_terms(resume_text)
    job_desc_terms = extract_key_terms(job_desc_text)
    resume_terms_text = ' '.join(resume_terms)
    job_desc_terms_text = ' '.join(job_desc_terms)
    similarity = calculate_similarity(resume_terms_text, job_desc_terms_text)

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
