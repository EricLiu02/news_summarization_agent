from flask import Flask, render_template, jsonify, request, session
from scraper import get_all_articles
from analyzer import NewsAnalyzer
from voice_agent import VoiceAgent
import os
from dotenv import load_dotenv
import json
import tempfile
from elevenlabs import save
import base64
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'news_summarization_secret_key')

# Initialize API keys from environment
NYT_API_KEY = os.getenv('NYT_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
ELEVEN_API_KEY = os.getenv('ELEVEN_API_KEY')
ELEVEN_VOICE_ID = os.getenv('ELEVEN_VOICE_ID')
VOICE_NAME = os.getenv('VOICE_NAME')
VOICE_STABILITY = float(os.getenv('VOICE_STABILITY', '0.71'))
VOICE_CLARITY = float(os.getenv('VOICE_CLARITY', '0.75'))
VOICE_STYLE = float(os.getenv('VOICE_STYLE', '0.6'))

# Default selected sections
DEFAULT_SECTIONS = ['world', 'business', 'technology', 'science', 'health']

# Cache for analysis results
news_cache = {
    'analysis': None,
    'report': None,
    'last_updated': None
}

def generate_audio_file(text, voice_agent):
    """Generate audio file from text using ElevenLabs"""
    try:
        # Use the voice settings from the agent
        voice_settings = {
            "stability": voice_agent.stability,
            "similarity_boost": voice_agent.clarity,
            "style": voice_agent.style,
            "use_speaker_boost": True
        }
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            audio_path = temp_file.name
        
        print(f"Generating audio for text of length {len(text)}...")
        
        # Generate audio
        audio = voice_agent.generate_audio(text)
        
        if not audio:
            print("Failed to generate audio: received None from voice_agent.generate_audio")
            return None
            
        print(f"Audio generated, saving to {audio_path}...")
        
        # Save audio to file
        save(audio, audio_path)
        
        print(f"Audio saved successfully ({os.path.getsize(audio_path)} bytes)")
        return audio_path
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        traceback.print_exc()
        return None

@app.route('/')
def index():
    """Render the main page"""
    user_name = session.get('user_name', '')
    selected_sections = session.get('selected_sections', DEFAULT_SECTIONS)
    return render_template('index.html', user_name=user_name, selected_sections=selected_sections)

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    """Update user preferences"""
    data = request.form
    
    # Save user name
    session['user_name'] = data.get('user_name', '')
    
    # Save selected sections
    selected_sections = data.getlist('sections')
    if not selected_sections:  # Make sure at least one section is selected
        selected_sections = DEFAULT_SECTIONS
    session['selected_sections'] = selected_sections
    
    print(f"Updated preferences: user_name={session['user_name']}, sections={selected_sections}")
    
    return jsonify({'status': 'success'})

@app.route('/get_news')
def get_news():
    """Get news data and analysis"""
    global news_cache
    
    # Check if we need to refresh the cache
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if refresh or not news_cache['analysis']:
        try:
            # Fetch and analyze news
            news_data = get_all_articles(NYT_API_KEY)
            analyzer = NewsAnalyzer(api_key=CLAUDE_API_KEY)
            analysis = analyzer.analyze_news_data(news_data)
            report = analyzer.generate_summary_report(analysis)
            
            # Update cache
            from datetime import datetime
            news_cache = {
                'analysis': analysis,
                'report': report,
                'last_updated': datetime.now().isoformat()
            }
            
            return jsonify({
                'status': 'success',
                'analysis': analysis,
                'report': report,
                'last_updated': news_cache['last_updated']
            })
        except Exception as e:
            print("Error fetching news:", e)
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    else:
        return jsonify({
            'status': 'success',
            'analysis': news_cache['analysis'],
            'report': news_cache['report'],
            'last_updated': news_cache['last_updated']
        })

@app.route('/get_headlines_audio')
def get_headlines_audio():
    """Generate audio for headlines"""
    global news_cache
    
    if not ELEVEN_API_KEY:
        return jsonify({
            'status': 'error',
            'message': 'ElevenLabs API key not configured'
        })
    
    try:
        print("Generating headlines audio...")
        
        # Initialize voice agent
        print(f"Initializing voice agent with voice_id={ELEVEN_VOICE_ID}, voice_name={VOICE_NAME}")
        voice_agent = VoiceAgent(
            api_key=ELEVEN_API_KEY,
            voice_id=ELEVEN_VOICE_ID,
            voice_name=VOICE_NAME,
            stability=VOICE_STABILITY,
            clarity=VOICE_CLARITY,
            style=VOICE_STYLE
        )
        
        # Set user name if available
        user_name = session.get('user_name', '')
        if user_name:
            print(f"Setting user name to: {user_name}")
            voice_agent.set_user_name(user_name)
        
        # Get user's selected sections
        selected_sections = session.get('selected_sections', DEFAULT_SECTIONS)
        selected_sections = [s.lower() for s in selected_sections]  # Normalize to lowercase
        print(f"Selected sections: {selected_sections}")
        
        # Make sure we have news data
        if not news_cache['analysis']:
            print("No news data in cache, fetching...")
            response = get_news()
            data = json.loads(response.get_data(as_text=True))
            if data['status'] != 'success':
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to fetch news data'
                })
        
        # Prepare headlines and sections
        all_headlines = []
        all_sections = []
        
        for section, data in news_cache['analysis']['sections'].items():
            # Skip sections not selected by the user
            if section.lower() not in selected_sections:
                print(f"Skipping section {section}: not selected by user")
                continue
                
            if not data or 'recent_headlines' not in data:
                print(f"Skipping section {section}: missing data")
                continue
                
            # Filter out empty headlines
            headlines = [h for h in data.get('recent_headlines', []) if h and h.strip()]
            
            if not headlines:
                print(f"Skipping section {section}: no valid headlines")
                continue
                
            # Take only the first few headlines from each section
            for headline in headlines[:3]:
                if headline and headline.strip():
                    all_headlines.append(headline)
                    all_sections.append(section.capitalize())
        
        if not all_headlines:
            return jsonify({
                'status': 'error',
                'message': 'No headlines found for selected sections'
            })
        
        print(f"Found {len(all_headlines)} headlines across {len(set(all_sections))} sections")
        
        # Create custom script for headlines
        greeting = voice_agent.get_greeting()
        
        # Include selected sections in greeting
        section_names = ", ".join([s.capitalize() for s in selected_sections])
        script = f"{greeting}\n\nHere are today's top headlines from {section_names}:"
        
        # Group headlines by section
        section_grouped = {}
        for i, headline in enumerate(all_headlines):
            section = all_sections[i]
            if section not in section_grouped:
                section_grouped[section] = []
            section_grouped[section].append(headline)
        
        # Format headlines by section - only sections with headlines
        for section, section_headlines in section_grouped.items():
            if section_headlines and len(section_headlines) > 0:
                script += f"\n\nFrom {section}:"
                for i, headline in enumerate(section_headlines):
                    script += f"\n{headline}"
        
        script += "\n\nThat concludes today's headlines."
        
        print(f"Generated script with {len(script)} characters")
        
        # Generate audio
        audio_path = generate_audio_file(script, voice_agent)
        
        if audio_path and os.path.exists(audio_path):
            # Read the audio file and encode as base64
            print(f"Reading audio file from {audio_path}")
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_size = len(audio_data)
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up the temporary file
            os.unlink(audio_path)
            
            print(f"Returning audio data ({audio_size} bytes)")
            return jsonify({
                'status': 'success',
                'audio': audio_base64,
                'script': script
            })
        else:
            print("Failed to generate or save audio file")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate audio'
            })
    
    except Exception as e:
        print(f"Error generating headlines audio: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/get_report_audio')
def get_report_audio():
    """Generate audio for full report"""
    global news_cache
    
    if not ELEVEN_API_KEY:
        return jsonify({
            'status': 'error',
            'message': 'ElevenLabs API key not configured'
        })
    
    try:
        # Initialize voice agent
        voice_agent = VoiceAgent(
            api_key=ELEVEN_API_KEY,
            voice_id=ELEVEN_VOICE_ID,
            voice_name=VOICE_NAME,
            stability=VOICE_STABILITY,
            clarity=VOICE_CLARITY,
            style=VOICE_STYLE
        )
        
        # Set user name if available
        user_name = session.get('user_name', '')
        if user_name:
            voice_agent.set_user_name(user_name)
        
        # Format report
        script = f"Here's your in-depth news analysis and summary:\n\n{news_cache['report']}"
        
        # Generate audio
        audio_path = generate_audio_file(script, voice_agent)
        
        if audio_path:
            # Read the audio file and encode as base64
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up the temporary file
            os.unlink(audio_path)
            
            return jsonify({
                'status': 'success',
                'audio': audio_base64,
                'script': script
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate audio'
            })
    
    except Exception as e:
        print(f"Error generating report audio: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)