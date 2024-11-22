# main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import uuid
from weasyprint import HTML
from dotenv import load_dotenv
import logging
import requests
from starlette.background import BackgroundTask

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResumeRequest(BaseModel):
    experience: str
    job_description: str
    prompt: str

# Set your Hugging Face API token as an environment variable
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")

# Simple text generation function using Hugging Face Inference API
def generate_text(experience: str, job_description: str, prompt: str) -> str:
    if not HUGGING_FACE_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Hugging Face API token not configured"
        )
    
    model = "gpt2"  # Most reliable free model
    
    # Very structured prompt to help guide the model
    formatted_prompt = f"""Write a resume. Follow this EXACT format:

SUMMARY
Experienced Senior Software Engineer with strong background in backend development and system architecture. Specializing in {job_description}. Proven track record of leading teams and delivering high-performance solutions.

EXPERIENCE
{experience}

SKILLS
1. Backend Development
2. System Architecture
3. Team Leadership
4. Cloud Computing
5. Performance Optimization

ACHIEVEMENTS
1. Led team of 5 engineers
2. Improved system performance by 40%
3. Implemented CI/CD pipeline"""
    
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_length": 200,  # Shorter to avoid loops
            "temperature": 0.3,  # Lower temperature for more focused output
            "top_p": 0.8,
            "do_sample": True,
            "return_full_text": False,
            "repetition_penalty": 1.2  # Help prevent repetition
        }
    }

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                text = result[0].get("generated_text", "").strip()
                
                # If generation failed, return template
                if len(text) < 50 or text.count("SUMMARY") != 1:
                    return formatted_prompt
                return text
                
        # If API call failed, return template
        return formatted_prompt
            
    except Exception as e:
        logging.error(f"Error generating resume: {str(e)}")
        # Return template on error
        return formatted_prompt

def convert_to_html(text):
    text = re.sub(r'(\d+[\d,]*(?:\.\d+)?%?)', r'<b>\1</b>', text)
    html_text = "<html><body><p>" + text.replace("\n", "<br>") + "</p></body></html>"
    return html_text

@app.post("/generate_resume")
async def generate_resume(request: ResumeRequest):
    try:
        resume_text = generate_text(
            experience=request.experience,
            job_description=request.job_description,
            prompt=request.prompt
        )
        
        html_content = """
        <html>
        <body style='font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;'>
        """
        
        # Skip the instruction line
        skip_line = "Write a resume. Follow this EXACT format:"
        
        for line in resume_text.split('\n'):
            line = line.strip()
            if not line or line == skip_line:  # Skip empty lines and the instruction
                continue
                
            if line in ["SUMMARY", "EXPERIENCE", "SKILLS", "ACHIEVEMENTS"]:
                html_content += f"<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db;'>{line}</h2>"
            elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                html_content += f"<li style='margin: 10px 0;'>{line[3:]}</li>"
            else:
                html_content += f"<p style='margin: 10px 0;'>{line}</p>"
        
        html_content += "</body></html>"
        
        return {"resume_html": html_content}
        
    except Exception as e:
        logging.exception("Error in resume generation")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_pdf")
async def generate_pdf(request: ResumeRequest):
    try:
        # First generate the resume HTML
        resume_text = generate_text(
            experience=request.experience,
            job_description=request.job_description,
            prompt=request.prompt
        )
        
        # Create a more styled HTML for PDF
        html_content = """
        <html>
        <head>
            <style>
                @page {
                    margin: 1in;
                }
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                }
                h2 {
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 5px;
                    margin-top: 20px;
                }
                li {
                    margin: 8px 0;
                    list-style-type: disc;
                }
                p {
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
        """
        
        # Skip the instruction line and format the content
        skip_line = "Write a resume. Follow this EXACT format:"
        
        for line in resume_text.split('\n'):
            line = line.strip()
            if not line or line == skip_line:
                continue
                
            if line in ["SUMMARY", "EXPERIENCE", "SKILLS", "ACHIEVEMENTS"]:
                html_content += f"<h2>{line}</h2>"
            elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                html_content += f"<li>{line[3:]}</li>"
            else:
                html_content += f"<p>{line}</p>"
        
        html_content += "</body></html>"
        
        # Create a unique filename in a temporary directory
        filename = f"/tmp/resume_{uuid.uuid4()}.pdf"
        
        # Convert HTML to PDF
        HTML(string=html_content).write_pdf(filename)
        
        # Return the PDF file and clean up afterwards
        return FileResponse(
            filename,
            media_type="application/pdf",
            filename="resume.pdf",
            background=BackgroundTask(lambda: os.remove(filename))
        )
        
    except Exception as e:
        logging.exception("Error generating PDF")
        if 'filename' in locals():  # Clean up file if it was created
            try:
                os.remove(filename)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
