from sentence_transformers import SentenceTransformer, util
import os

# Use a lightweight model for speed
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def compute_resume_job_score(resume_text, job_text):
    model = get_model()
    resume_emb = model.encode(resume_text, convert_to_tensor=True)
    job_emb = model.encode(job_text, convert_to_tensor=True)
    score = util.pytorch_cos_sim(resume_emb, job_emb).item()
    # Convert to 0-100 for compatibility
    return int(score * 100)
