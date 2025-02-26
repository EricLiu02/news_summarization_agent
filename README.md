# News Summarization Agent with Voice

A Python application that fetches news articles from various sources, analyzes them using Claude AI, and generates insightful summary reports that can be read aloud by a personalized voice agent.

![News Summarization Agent](https://example.com/news_summarizer_screenshot.jpg)

## Features

- Fetches top stories from the New York Times API across multiple sections
- Scrapes and parses article content using newspaper3k
- Analyzes news data to extract key themes and trends using Claude AI
- Generates comprehensive summary reports
- Reads headlines and reports aloud using ElevenLabs text-to-speech with personalized voices
- Web interface for easy interaction

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/news_summarization_agent.git
   cd news_summarization_agent
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your actual API keys and voice preferences.

## Usage

### Web Interface (recommended)

1. Make sure your API keys are in the `.env` file
2. Run the web application:
   ```
   python app.py
   ```
3. Open your browser and navigate to `http://localhost:5000`
4. Enter your name for personalization (optional)
5. Click the "Listen to Headlines" button to hear today's top news

### Command Line Interface

You can also run the application from the command line:
```
python main.py
```

#### Voice Customization Options

```
python main.py --voice-name "Rachel" --user-name "Jane"
```

### Text-Only Mode

If you don't want voice features or don't have an ElevenLabs API key, run in text-only mode:
```
python main.py --text-only
```

## Requirements

- Python 3.6+
- New York Times API key (get one at https://developer.nytimes.com/)
- Anthropic Claude API key (get one at https://www.anthropic.com/)
- ElevenLabs API key (get one at https://elevenlabs.io/) - optional for voice features

## Structure

- `scraper.py`: Functions for scraping articles and fetching from NYT API
- `analyzer.py`: NewsAnalyzer class for analyzing articles and generating reports
- `voice_agent.py`: VoiceAgent class for personalized text-to-speech functionality
- `main.py`: Command-line interface
- `app.py`: Web application with Flask
- `templates/`: HTML templates for the web interface
- `.env.example`: Template for environment variables
- `.gitignore`: Prevents sensitive information from being committed to git

## Web Interface

The web interface provides a user-friendly way to interact with the news summarization agent:

- **Personalization**: Enter your name for customized greetings
- **Headlines View**: See the top headlines from each news section
- **Audio Playback**: Listen to headlines and full reports read aloud
- **Full Report**: Read the comprehensive news analysis

## API Endpoints

The web application exposes the following API endpoints:

- `/get_news`: Fetches and analyzes news articles
- `/get_headlines_audio`: Generates audio for headlines
- `/get_report_audio`: Generates audio for the full report
- `/update_preferences`: Updates user preferences

## Deployment

To deploy the web application to a production server:

1. Set up your environment variables
2. Use a WSGI server like Gunicorn:
   ```
   gunicorn app:app
   ```

## How It Works

1. The application fetches top news stories from the New York Times API
2. Claude AI analyzes the news data to identify key themes and trends
3. A comprehensive summary report is generated
4. The web interface allows users to view and listen to the news
5. ElevenLabs voice synthesis provides natural-sounding audio