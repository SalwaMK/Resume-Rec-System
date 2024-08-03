import streamlit as st
import requests
import time
from backend import insert_similarity_data

def main():
    st.title('Resume-Job Description Similarity App')
    col1, col2, col3 = st.columns([1, 50, 1])
    col2.markdown("##### Match your resume with the job description")

    uploaded_file = col2.file_uploader("Upload your resume", type=["pdf"])
    category = col2.selectbox('Select job description category:',
                              ['product_manager', 'frontend_engineer', 'full_stack_engineer'])

    if uploaded_file is not None:
        if col2.button('Send Resume!'):
            progress_bar = col2.progress(0)
            for perc_completed in range(100):
                time.sleep(0.03)
                progress_bar.progress(perc_completed + 1)

            col2.success("File uploaded successfully")

            files = {'file': uploaded_file}
            data = {'category': category}

            try:
                response = requests.post('http://localhost:5000/upload', files=files, data=data)
                response.raise_for_status()  # Raise an exception for HTTP errors

                result = response.json()
                similarity_score = result.get('similarity_score')
                resume_terms = result.get('resume_terms', [])
                job_desc_terms = result.get('job_desc_terms', [])

                st.write(f'## Similarity Score: {similarity_score}')
                print(similarity_score)
                with st.expander("Click to read more"):
                    st.write("## Resume terms:")
                    for term in resume_terms:
                        st.write(term)
                    st.write("## Job description terms:")
                    for term in job_desc_terms:
                        st.write(term)

                #***
                insert_similarity_data(uploaded_file.name, category, similarity_score, resume_terms, job_desc_terms)

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to process the request. Error: {e}")

if __name__ == '__main__':
    main()
