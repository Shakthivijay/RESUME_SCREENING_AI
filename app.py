import streamlit as st
import requests
import os
import PyPDF2
import docx
import re
import time
from dotenv import load_dotenv  

load_dotenv()

# First, check environment variable from GitHub Actions, then fallback to .env file
API_KEY = os.getenv("MISTRAL_API_KEY")

if not API_KEY:
    print("API Key Not Found! Check your environment variables.")
    st.error("❌ API Key not found! Please set it ")
    st.stop()

API_URL = "https://api.mistral.ai/v1/chat/completions"

# Function to extract text from a PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = "".join(page.extract_text() + "\n" for page in pdf_reader.pages)
    return text

# Function to extract text from a DOCX file
def extract_text_from_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

# List of actual technical skills for filtering
TECHNICAL_SKILLS = {
    "html", "css", "javascript", "reactjs", "nodejs", "angular", "vuejs", "git", "github",
    "restful", "apis", "backend", "frontend", "python", "java", "c++", "sql", "mongodb",
    "expressjs", "typescript", "flutter", "django", "flask", "devops", "docker", "kubernetes",
    "machine learning", "tensorflow", "pytorch", "data structures", "algorithms",
    "unit testing", "debugging", "oop", "firebase", "graphql", "ci/cd", "scalability"
}

# Function to extract keywords
def extract_keywords(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    words = text.split()
    return set(words)

# Function to filter technical skills
def get_filtered_missing_skills(resume_text, job_description):
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)

    # Filter only technical skills from resume and job description
    matched_skills = resume_keywords.intersection(job_keywords).intersection(TECHNICAL_SKILLS)
    missing_skills = job_keywords.difference(resume_keywords).intersection(TECHNICAL_SKILLS)

    return matched_skills, missing_skills

# Function to calculate resume score (out of 100)
def calculate_resume_score(matched_skills, job_keywords):
    total_job_skills = len(job_keywords)
    if total_job_skills == 0:
        return 0
    return min(100, round((len(matched_skills) / total_job_skills) * 100, 2))  # Ensure it never exceeds 100%

# Function to get AI suggestions from Mistral
def get_resume_suggestions(resume_text, job_description):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-tiny",
        "messages": [
            {"role": "system", "content": "You are an AI resume analyzer. Give detailed suggestions to improve resumes."},
            {"role": "user", "content": f"Resume: {resume_text}\n\nJob Description: {job_description}"}
        ]
    }

    response = requests.post(API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return f"❌ API Error {response.status_code}: {response.text}"

# Custom CSS for animations and styling
st.markdown("""
    <style>
        .stApp {
            background-image: linear-gradient(to right top, #b503bc, #a326c5, #8f36cc, #7842d2, #5d4bd6);
            color: white;
        }

        .glass-box {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 10px rgba(255, 255, 255, 0.2);
        }

        .score-container {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            color: #fff;
            padding: 15px;
            background: rgba(0, 0, 0, 0.6);
            border-radius: 10px;
            backdrop-filter: blur(5px);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 80px;
            width: 100%;
            position: relative;
            overflow: hidden;
            flex-direction: column;
        }

        /* Loading Animation */
        .loader {
            width: 100%;
            height: 12px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
            margin-top: 10px;
        }

        .loader::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 0;
            background: linear-gradient(to right, #00c6ff, #0072ff);
            box-shadow: 0 0 10px #0072ff;
            animation: loadExpand 2s ease-in-out forwards;
        }

        @keyframes loadExpand {
            0% { width: 0; }
            100% { width: 100%; }
        }
        
    </style>
""", unsafe_allow_html=True)

# Sidebar for File Upload, Job Description, and Button
with st.sidebar:
    st.title("📄 AI Resume Optimizer")
    uploaded_file = st.file_uploader("📤 Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])
    job_description = st.text_area("📝 Enter Job Description")
    analyze_button = st.button("🔍 Check My Resume")

# Main Content
st.title("📋 Resume Analysis")

if analyze_button:
    if uploaded_file and job_description:
        resume_text = extract_text_from_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else extract_text_from_docx(uploaded_file)

        matched_skills, filtered_missing_skills = get_filtered_missing_skills(resume_text, job_description)

        # Resume Score Calculation (out of 100)
        resume_score = calculate_resume_score(matched_skills, extract_keywords(job_description))

        # Resume Score with Dynamic Loader
        with st.container():
            st.subheader("🎯 Resume Score")
            score_placeholder = st.empty()

            # Show animated loading bar first
            score_placeholder.markdown(
                f'''
                <div class="score-container">
                    <div class="loader"></div>
                </div>
                ''', 
                unsafe_allow_html=True
            )

            time.sleep(2)  # Simulating animation time

            # Display the actual score after loading animation
            score_placeholder.markdown(f'<div class="score-container"> {resume_score}% Matched</div>', unsafe_allow_html=True)

        # Matched Skills
        st.subheader("✅ Matched Skills")
        st.markdown(f'<div class="glass-box">{", ".join(matched_skills) if matched_skills else "No matching skills found."}</div>', unsafe_allow_html=True)

        # Missing Skills
        st.subheader("⚠️ Missing Skills")
        st.markdown(f'<div class="glass-box">{", ".join(filtered_missing_skills) if filtered_missing_skills else "No missing skills found."}</div>', unsafe_allow_html=True)

        # AI Suggestions
        st.subheader("🤖 ResumeBoost AI")
        ai_suggestions = get_resume_suggestions(resume_text, job_description)
        st.markdown(f'<div class="glass-box">💡 {ai_suggestions}</div>', unsafe_allow_html=True)
    else:
        st.error("❗ Please upload a resume and enter a job description before clicking 'Check My Resume'.")
