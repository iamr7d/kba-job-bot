import pdfplumber
import google.generativeai as genai
import os

# Set your Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBX7vWcp12eIX9g8Sa2TE4yYK3imbi2gMM")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Path to your resume PDF
resume_path = r"C:\Users\rahul\OneDrive\Desktop\PHD\CV_CDT_RAHULRAJ_P_V___RESUME___JANUARY_2025__Copy_.pdf"

# Extract text from PDF
with pdfplumber.open(resume_path) as pdf:
    resume_text = " ".join([page.extract_text() or "" for page in pdf.pages])

import re
prompt = f"""
You are a professional resume reviewer and job recommender.
Given the following resume, reply in this STRICT JSON format:
{{
  'rating': <number>,
  'improvement': <1 line string>,
  'jobs': [<job1>, <job2>, <job3>]
}}
Do NOT explain, do NOT add extra keys, do NOT use nested objects.
Always give the SAME rating for the SAME resume (be deterministic and consistent).
Example:
{{'rating': 82, 'improvement': 'Add more quantifiable achievements.', 'jobs': ['AI Engineer', 'Data Scientist', 'ML Researcher']}}
Now, for the following resume:
{resume_text[:4000]}
"""

for i in range(3):
    print(f"\n--- Run {i+1} ---")
    try:
        response = model.generate_content(prompt)
        result = response.text if hasattr(response, 'text') else str(response)
        match = re.search(r'\{.*\}', result, re.DOTALL)
        json_str = match.group(0) if match else result
        import json
        parsed = json.loads(json_str.replace("'", '"'))
        print(f"Rating: {parsed.get('rating', 'N/A')}")
        print(f"Improvement: {parsed.get('improvement', '')}")
        print(f"Jobs: {parsed.get('jobs', [])}")
    except Exception as e:
        print(f"[Gemini API Error] {e}")
