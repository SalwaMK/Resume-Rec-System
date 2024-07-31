import streamlit as st
import requests
import time


def main():
    st.title('Resume-Job Description Similarity App')
    col1, col2, col3 = st.columns([1, 50, 1])
    col2.markdown("# Match your resume with the job description")

    uploaded_file = col2.file_uploader("Upload your resume", type=["pdf"])
    category = col2.selectbox('Select job description category:',
                              ['product_manager', 'data_scientist', 'software_engineer'])

    if uploaded_file is not None:
        if st.button('Send Resume!'):
            progress_bar = col2.progress(0)
            for perc_completed in range(100):
                time.sleep(0.03)
                progress_bar.progress(perc_completed + 1)

            files = {'file': uploaded_file}
            data = {'category': category}

            response = requests.post('http://localhost:5000/upload', files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                similarity_score = result.get('similarity_score')
                resume_terms = result.get('resume_terms', [])
                job_desc_terms = result.get('job_desc_terms', [])

                st.write(f'## Similarity Score: {similarity_score}')
                with st.expander("Click to read more"):
                    st.write("## Resume terms:")
                    for term in resume_terms:
                        st.write(term)
                    st.write("## Job description terms:")
                    for term in job_desc_terms:
                        st.write(term)
            else:
                st.error("Failed to process the request. Please try again.")


if __name__ == '__main__':
    main()
