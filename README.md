# Resume-Job Description Similarity App

## Description

This project is a web application that allows users to upload a resume and match it with a job description to calculate a similarity score. The application uses Flask for the backend, Streamlit for the frontend, and a REST API for communication between the frontend and backend. The similarity score and extracted data are stored in a MySQL database.

## Features

- Upload resume files (PDF format)
- Select job description category
- Calculate similarity score between resume and job description
- Display similarity score and key terms from both resume and job description
- Store similarity score and extracted data in a MySQL database

## Prerequisites

- Python 3.7+
- MySQL server

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/resume-job-description-similarity-app.git
   cd resume-job-description-similarity-app
   
2. **Create and activate a virtual environment (optional but recommended):**
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows use `$venv\Scripts\activate`

3. **Install the required dependencies:**
  ```bash
  pip install -r requirements.txt

4. **Set up the MySQL database:**
- Create a MySQL database named cv-matcher.
- Create the necessary tables:
CREATE TABLE files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(255),
    path VARCHAR(255)
);

CREATE TABLE similarities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(255),
    similarity_score FLOAT,
    resume_terms TEXT,
    job_desc_terms TEXT
);

- Insert some job description files into the files table.

##Usage
1. **Run the backend server:**
  ````bash
  python backend.py

2. **Run the frontend application:**
  `````bash
  streamlit run frontend.py

3. **Access the application:**
Open your web browser and go to http://localhost:8501/

4. **Use the application:**
- Upload a resume file (PDF).
- Select a job description category.
- Click on the "Send Resume!" button to calculate the similarity score.
