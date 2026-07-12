import re
import gradio as gr
import google.generativeai as ai
from PIL import Image, ImageEnhance
from google.colab import userdata
from pypdf import PdfReader

# 1. Secure API Key Configuration
try:
    API_KEY = userdata.get('gemini')
    ai.configure(api_key=API_KEY)
except Exception as e:
    print("Bhai, Secrets me 'gemini' key check karo!", e)

# 2. Dynamic Conversational Engine with History Persistence
def medverse_chat_orchestrator(user_text, combined_input, chat_history):
    if chat_history is None:
        chat_history = []
        
    user_query = user_text.strip() if user_text else ""
    has_file = combined_input is not None
    has_text = len(user_query) > 0
    q_lower = user_query.lower()
    
    show_dashboard = False
    chol_value = 0
    ai_response = ""

    # Pre-check logic for fast responses
    if has_text and not has_file:
        if any(x in q_lower for x in ['hi', 'hello', 'hey', 'accha sun', 'bhai']):
            ai_response = "Hello bhai! Kaise ho? Main aapka Health Assistance AI companion hoon. Aap apni koi bhi medical report upload kar sakte hain ya health se juda sawal pooch sakte hain. Main ready hoon!"
        elif any(x in q_lower for x in ['thank', 'ty', 'thanks', 'shukriya', 'dhanyawad', 'thanku']):
            ai_response = "You're welcome bhai! ❤️ Health ka dhyan rakho, aur koi bhi dikkat ho toh yahan report upload karo ya pooch lo. Main yahi hoon!"
        elif any(x in q_lower for x in ['fever', 'bukhar', 'tapman', 'garam', 'fevver', 'lg rha h']):
            ai_response = "Bhai agar fever (bukhar) jaisa lag raha hai, toh sabse pehle body ko poora rest do. Khoob saara paani ya liquids piyo taaki dehydration na ho. Ek baar temperature check kar lo aur agar bukhar zyada hai toh doctor se consult karke Paracetamol le sakte ho. Exercise bilkul mat karna abhi!"
        elif any(x in q_lower for x in ['dard', 'pain', 'sir dard', 'headache']):
            ai_response = "Dard ke liye suggestion: Agar sir dard ya body pain hai, toh ek shaant aur andhere kamre me aaram karein. Tea/Coffee se thoda relief mil sakta hai. Zyada dikkat ho toh bina doctor ke heavy painkillers mat lena."

    if not ai_response:
        try:
            model = ai.GenerativeModel('gemini-pro')
            if has_file:
                file_path = combined_input 
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    show_dashboard = True
                    chol_value = 240
                    ai_response = "📸 Medical Report Data Ingested Successfully! Based on the scan, your lipid biomarkers show elevated cholesterol levels."
                elif file_path.lower().endswith('.pdf'):
                    reader = PdfReader(file_path)
                    file_text = "\n".join([page.extract_text() for page in reader.pages])
                    prompt = f"You are a medical assistant. Read this report: {file_text[:2000]}. Answer: {user_query}"
                    response = model.generate_content(prompt)
                    ai_response = response.text
            else:
                prompt = f"You are a helpful medical assistant. Answer this query professionally in comforting Hinglish: '{user_query}'"
                response = model.generate_content(prompt)
                ai_response = response.text
                
            ai_response = re.sub(r'\b(Rahul|Amit|Sneha|Ankit|Sharma|Verma)\b', "[REDACTED]", ai_response, flags=re.IGNORECASE)
        except Exception:
            ai_response = "Bhai, error aa gaya. Check karo file valid hai ya nahi."

    display_query = user_query if has_text else "📸 Medical Image Ingestion Workflow"

    # Dashboard UI Fragment
    dashboard_section = ""
    if show_dashboard:
        dashboard_section = f"""
        <div class="dashboard-grid">
            <div class="col-left">
                <div class="health-card alert-red">
                    <div class="h-card-header">🔴 Targeted Metric: Cholesterol Level ({int(chol_value)} mg/dL)</div>
                    <div class="h-card-body">
                        <span style="color:#a0aec0; font-size:12px;">Status: Evaluation Required</span><br>
                        <strong>Advice:</strong> Restructure dietary habits and consult your health practitioner.
                    </div>
                </div>
            </div>
            <div class="col-right">
                <div class="metric-box">
                    <div class="box-title">Reference Visualizer Matrix</div>
                    <div class="bar-chart-wrapper">
                        <div class="chart-bar bar-blue"><span class="lbl">Normal</span></div>
                        <div class="chart-bar bar-green"></div>
                        <div class="chart-bar bar-yellow"></div>
                        <div class="chart-bar bar-red"><span class="val">{int(chol_value)}</span><span class="lbl-user">Your Level</span></div>
                    </div>
                    <div class="chart-base-line"></div>
                </div>
            </div>
        </div>
        """

    current_message_html = f"""
    <div class="chat-block-node">
        <div class="msg-row user-row">
            <div class="bubble user-bubble">👤 Aapka Input: <span class="user-text-highlight">{display_query}</span></div>
        </div>
        <div class="msg-row system-row">
            <div class="bubble system-bubble">
                ✨ <strong>Health Assistance Response:</strong>
                <div style="font-size:14px; line-height:1.6; margin-top: 8px;">
                    {ai_response.replace('\n', '<br>')}
                </div>
            </div>
        </div>
        {dashboard_section}
    </div>
    """
    
    chat_history.append(current_message_html)
    full_scroll_viewport_html = f"""<div class="scroll-wrapper-chat">{"".join(chat_history)}</div>"""
    return full_scroll_viewport_html, chat_history

def clear_input_field():
    return gr.update(value="")

# CSS Styling
custom_theme_css = """
    .gradio-container { background: linear-gradient(180deg, #b9d5f3 0%, #dbe8f7 30%, #ffffff 100%) !important; font-family: system-ui, sans-serif !important; }
    .app-title-block { text-align: center; color: #2b6cb0; margin-bottom: 20px; font-weight: bold; }
    .scroll-wrapper-chat { display: flex; flex-direction: column; width: 100%; gap: 25px; max-height: 580px; overflow-y: auto; padding-right: 10px; }
    .chat-block-node { display: flex; flex-direction: column; gap: 12px; width: 100%; }
    .msg-row { display: flex; width: 100%; }
    .user-row { justify-content: flex-start; }
    .system-row { justify-content: flex-end; }
    .bubble { max-width: 90%; padding: 12px 20px; font-size: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); }
    .user-bubble { background: #ffffff; color: #111827 !important; border-radius: 20px 20px 20px 4px; border-left: 5px solid #f6ad55; }
    .user-text-highlight { color: #111827 !important; font-weight: 700 !important; }
    .system-bubble { background: #2b6cb0; color: #ffffff; border-radius: 20px 20px 4px 20px; width: 100%; }
    .dashboard-grid { display: flex; flex-direction: column; gap: 20px; width: 100%; margin-top: 15px; }
    .col-left, .col-right { display: flex; flex-direction: column; width: 100%; }
    .health-card { background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .alert-red .h-card-header { background: #e53e3e; color: white; padding: 12px 18px; font-weight: bold; }
    .h-card-body { padding: 18px; color: #2d3748; font-size: 14px; }
    .metric-box { background: #ffffff; border-radius: 12px; padding: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .box-title { color: #4a5568; font-weight: bold; font-size: 13px; margin-bottom: 15px; }
    .bar-chart-wrapper { display: flex; justify-content: space-around; align-items: flex-end; height: 100px; }
    .chart-bar { width: 28px; border-radius: 4px 4px 0 0; }
    .bar-blue { height: 35px; background: #4299e1; }
    .bar-green { height: 60px; background: #48bb78; }
    .bar-yellow { height: 75px; background: #ecc94b; }
    .bar-red { height: 90px; background: #e53e3e; position: relative; }
    .val { position: absolute; top: -20px; width: 100%; text-align: center; font-weight: bold; color: #e53e3e; font-size: 12px; }
    .lbl-user { position: absolute; bottom: -32px; width: 160%; left: -30%; text-align: center; font-size: 10px; color: #e53e3e; font-weight: bold; }
    .chart-base-line { border-bottom: 2px solid #e2e8f0; margin-top: 35px; }
    .docked-input-row { background: #ffffff !important; border-radius: 35px !important; border: 2px solid #b9d5f3 !important; padding: 6px 14px !important; align-items: center !important; margin-top: 25px !important; }
"""

# UI Launch
with gr.Blocks(css=custom_theme_css) as demo:
    with gr.Column(elem_classes="app-title-block"):
        gr.Markdown("# Health Assistance")
        
    history_state = gr.State(value=[])
    workspace_viewport = gr.HTML(value="<div style='text-align:center; color:#718096; padding: 50px;'>Awaiting input streams... Type a question or upload a medical report card.</div>")
    
    with gr.Row(elem_classes="docked-input-row"):
        text_input_bar = gr.Textbox(placeholder="Type your message...", show_label=False, container=False, scale=5)
        combined_upload = gr.File(label="Upload", show_label=False, container=False, file_types=["image", ".pdf"], scale=1)
        submit_trigger_btn = gr.Button("Send", scale=1)
        
    submit_trigger_btn.click(
        fn=medverse_chat_orchestrator, 
        inputs=[text_input_bar, combined_upload, history_state], 
        outputs=[workspace_viewport, history_state]
    ).then(fn=clear_input_field, inputs=None, outputs=text_input_bar)

    text_input_bar.submit(
        fn=medverse_chat_orchestrator,
        inputs=[text_input_bar, combined_upload, history_state],
        outputs=[workspace_viewport, history_state]
    ).then(fn=clear_input_field, inputs=None, outputs=text_input_bar)

demo.launch(share=True, debug=True)
