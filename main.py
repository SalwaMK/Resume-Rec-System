import streamlit as st
import fitz
import spacy
import textacy
from sentence_transformers import SentenceTransformer, util
import mysql.connector
import time
import os
import json

#to extract text from PDF
def extract_text_from_pdf(pdf_path):
    if isinstance(pdf_path, bytearray):
        pdf_path = pdf_path.decode('utf-8')
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


#to load the spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("Downloading language model for the spaCy library...")
    from spacy.cli import download

    download("en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')


#to extract key terms using TextRank
def extract_key_terms(text):
    doc = nlp(text)
    key_terms = textacy.extract.keyterms.textrank(doc, normalize="lemma", topn=50)
    return [term for term, _ in key_terms]


#to initialize SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')


#to calculate similarity
def calculate_similarity(text1, text2):
    embed1 = model.encode(text1, convert_to_tensor=True)
    embed2 = model.encode(text2, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embed1, embed2)
    return similarity.item()


#to connect to MySQL and retrieve data based on category
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
            st.error(f"No job description found for category: {category}")
            return None
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

#to initialize static id variable
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
        st.error(f"Error: {err}")
        return None


id = initialize_static_id()

#to insert similarity data into the database
def insert_similarity_data(name, category, similarity_score, resume_terms, job_desc_terms):
    global  id
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
        id-=1
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")


#to process and compare
def process_and_compare(resume_pdf, job_desc_pdf):
    resume_text = extract_text_from_pdf(resume_pdf)
    job_desc_text = extract_text_from_pdf(job_desc_pdf)
    resume_terms = extract_key_terms(resume_text)
    job_desc_terms = extract_key_terms(job_desc_text)
    resume_terms_text = ' '.join(resume_terms)
    job_desc_terms_text = ' '.join(job_desc_terms)
    similarity = calculate_similarity(resume_terms_text, job_desc_terms_text)

    return similarity, resume_terms, job_desc_terms


#streamlit app
def main():
    st.title('Resume-Job Description Similarity App')
    col1, col2, col3 = st.columns([1, 50, 1])
    col2.markdown("##### Match your resume with the job description")

    uploaded_file = col2.file_uploader("Upload your resume", type=["pdf"])
    category = col2.selectbox('Select job description category:',
                              ['product_manager', 'frontend_engineer', 'full_stack_engineer'])

    if uploaded_file is not None:
        with open(f"./Data/Resumes/{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())

        button_clicked = col2.button('Send Resume!')

        if button_clicked:
            progress_bar = col2.progress(0)
            for perc_completed in range(100):
                time.sleep(0.03)
                progress_bar.progress(perc_completed + 1)

            col2.success("File uploaded successfully")

            job_desc_pdf_path = get_job_description_path(category)
            if job_desc_pdf_path:
                if isinstance(job_desc_pdf_path, bytearray):
                    job_desc_pdf_path = job_desc_pdf_path.decode('utf-8')
                similarity_score, resume_terms, job_desc_terms = process_and_compare(
                    f"./Data/Resumes/{uploaded_file.name}", job_desc_pdf_path)

                # Insert similarity data into the database
                '''extracted_data = {
                    "resume_terms": resume_terms,
                    "job_desc_terms": job_desc_terms
                }'''

                insert_similarity_data(uploaded_file.name, category, similarity_score, resume_terms, job_desc_terms)

                st.write(f'## Similarity Score: {similarity_score}')

                with st.expander("Click to read more"):
                    st.write("## Resume terms:")
                    for term in resume_terms:
                        st.write(term)
                    st.write("## Job description terms:")
                    for term in job_desc_terms:
                        st.write(term)


if __name__ == '__main__':
    main()
