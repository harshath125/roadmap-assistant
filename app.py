# File: app.py
# Harsha's Career Compass - New Version

import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, Response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__, template_folder='templates')

def generate_ai_plan(goal, skill_level, skills_to_learn, hours_per_week):
    """
    Connects to the Gemini API and generates a learning plan.
    """
    try:
        # Securely get the API key from environment variables
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file or server environment.")
            
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"API Key Configuration Error: {e}")
        return None

    prompt = f"""
    You are an expert career coach. Your task is to generate ONLY a valid JSON object. Do not include markdown formatting like ```json or any text before or after the JSON object.

    The JSON must have one root key: "learning_plan". This key will contain an array of 8 objects, one for each week.
    Each weekly object must have these keys: "week", "topic", "details" (a list of strings), and "resources" (a list of strings).

    Create this 8-week plan for a user with these details:
    - Goal: "{goal}"
    - Skill Level: {skill_level}
    - Skills: {skills_to_learn}
    - Time Commitment: {hours_per_week} hours/week
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        
        print("--- Sending Prompt to Gemini ---")
        response = model.generate_content(prompt, generation_config=generation_config)
        print("--- Received Response ---")
        
        plan_data = json.loads(response.text)
        return plan_data
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Gemini API Feedback: {response.prompt_feedback}")
        return None

def create_pdf(plan_data):
    """Generates a PDF from the plan data."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=50, bottomMargin=50, leftMargin=50, rightMargin=50)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("Your Custom Career Compass Plan", styles['h1'])
    story.append(title)
    story.append(Spacer(1, 24))

    for week_data in plan_data.get('learning_plan', []):
        week_title = Paragraph(f"<b>{week_data['week']}: {week_data['topic']}</b>", styles['h2'])
        story.append(week_title)
        story.append(Spacer(1, 12))

        story.append(Paragraph("<b><u>Plan Details:</u></b>", styles['Normal']))
        for detail in week_data['details']:
            story.append(Paragraph(f"• {detail}", styles['Bullet']))
        
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b><u>Suggested Resources:</u></b>", styles['Normal']))
        for resource in week_data['resources']:
            story.append(Paragraph(f"• {resource}", styles['Bullet']))
            
        story.append(Spacer(1, 24))

    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    plan = generate_ai_plan(
        data.get('goal'),
        data.get('skillLevel'),
        data.get('skills'),
        data.get('hours')
    )
    if plan and 'learning_plan' in plan:
        return jsonify(plan)
    else:
        return jsonify({"error": "Failed to generate plan from AI. Check the server logs for details."}), 500

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    plan_data = request.json
    if not plan_data:
        return "Invalid data", 400
    pdf_buffer = create_pdf(plan_data)
    return Response(
        pdf_buffer,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment;filename=Career_Compass_Plan.pdf'}
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
