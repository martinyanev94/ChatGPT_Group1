from flask import Flask, render_template, request, send_file, session,redirect, url_for
import openai
from werkzeug.utils import secure_filename
import os
import config
import requests
from docx import Document  # Added import for working with docx

app = Flask(__name__)
app.secret_key = '1234@abcd'  # Secret key for session management

# Configure OpenAI API key
openai.api_key = config.API_KEY

# Define route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Essay Generation Route
@app.route('/essay', methods=['GET', 'POST'])
def essay():
    if request.method == 'POST':
        topic = request.form.get('topic')
        length = request.form.get('length')  # Fetch the length option
        tone = request.form.get('tone')  # Fetch the tone option

        # Request essay from GPT-3.5
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Write a {length}, {tone} essay on {topic}."}
            ]
        )
        essay_text = response['choices'][0]['message']['content']

        # Save the essay to a .docx file
        doc = Document()
        doc.add_paragraph(essay_text)
        file_path = os.path.join(app.root_path, 'static', 'generated_essay.docx')
        doc.save(file_path)

        # Render the essay on the page
        return render_template('essay.html', essay=essay_text, download_link='/static/generated_essay.docx')

    return render_template('essay.html')

# Image Generation Route
@app.route('/image', methods=['GET', 'POST'])
def image():
    if request.method == 'POST':
        description = request.form.get('description')
        # Generate the image using OpenAI API
        response = openai.Image.create(prompt=description, size="1024x1024")
        image_url = response['data'][0]['url']

        # Download the image using the 'requests' library
        image_file_path = os.path.join(app.root_path, 'static', 'generated_image.png')
        with requests.get(image_url, stream=True) as r:  # Use requests.get
            if r.status_code == 200:
                with open(image_file_path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            else:
                return f"Error downloading image: {r.status_code}", 500

        # Pass the image file path to the template
        return render_template('image.html', image_url=f'/static/generated_image.png')
    
    return render_template('image.html')

# Chatbot Route
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    # Initialize chat history if not present
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST':
        user_message = request.form.get('message')
        if user_message:
            try:
                # Call OpenAI API for chatbot response
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_message}]
                )
                bot_response = response['choices'][0]['message']['content']

                # Append user message and bot response to session chat history
                session['chat_history'].append({"user": user_message, "bot": bot_response})
                session.modified = True  # Mark session as modified

            except Exception as e:
                return render_template('chatbot.html', error_message=str(e), chat_history=session['chat_history'])

    # Render the chatbot template with current chat history
    return render_template('chatbot.html', chat_history=session['chat_history'])

# Clear Chat History Route
@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    print("Clearing chat history...")  # Debugging log
    session.pop('chat_history', None)  # Remove chat history from session
    session.modified = True  # Mark session as modified
    print("Chat history cleared.")  # Debugging log
    return redirect(url_for('chatbot'))  # Redirect back to chatbot page

# Audio Transcription Route
@app.route('/audio', methods=['GET', 'POST'])
def audio():
    if request.method == 'POST':
        audio_file = request.files['audio']
        file_path = secure_filename(audio_file.filename)
        audio_file.save(file_path)
        
        response = openai.Audio.transcribe("whisper-1", open(file_path, "rb"))
        transcription = response['text']
        
        # Save transcription to a text file
        transcript_path = os.path.join(app.root_path, 'static', 'transcription.txt')
        with open(transcript_path, 'w') as f:
            f.write(transcription)
        
        os.remove(file_path)
        return render_template('audio.html', transcription=transcription, transcript_link='/static/transcription.txt')
    return render_template('audio.html')


# Text Summarizer Route
@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if request.method == 'POST':
        text = request.form.get('text')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Summarize the following text: {text}"}]
        )
        summary_text = response.choices[0].message['content']
        return render_template('summary.html', summary=summary_text)
    return render_template('summary.html')


if __name__ == '__main__':
    app.run(debug=True)
