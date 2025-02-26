from scraper import get_all_articles
from analyzer import NewsAnalyzer
from voice_agent import VoiceAgent
import argparse
import os
from dotenv import load_dotenv

def main():
    """
    Main function to run the news summarization application.
    
    Loads API keys from environment variables or command-line arguments.
    Command-line arguments take precedence over environment variables.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup argument parser with environment variables as defaults
    parser = argparse.ArgumentParser(description='News Summarization Agent')
    parser.add_argument('--nyt-api-key', default=os.getenv('NYT_API_KEY'), 
                        help='New York Times API key (default: from NYT_API_KEY env var)')
    parser.add_argument('--claude-api-key', default=os.getenv('CLAUDE_API_KEY'), 
                        help='Claude API key (default: from CLAUDE_API_KEY env var)')
    parser.add_argument('--eleven-api-key', default=os.getenv('ELEVEN_API_KEY'),
                        help='ElevenLabs API key (default: from ELEVEN_API_KEY env var)')
    parser.add_argument('--eleven-voice-id', default=os.getenv('ELEVEN_VOICE_ID'),
                        help='ElevenLabs voice ID (default: from ELEVEN_VOICE_ID env var)')
    parser.add_argument('--voice-name', default=os.getenv('VOICE_NAME'),
                        help='ElevenLabs voice name to search for (default: from VOICE_NAME env var)')
    parser.add_argument('--user-name', default=os.getenv('USER_NAME', 'News Listener'),
                        help='Your name for personalized greetings (default: from USER_NAME env var)')
    parser.add_argument('--text-only', action='store_true',
                        help='Run in text-only mode (no voice output)')
    parser.add_argument('--list-voices', action='store_true',
                        help='List available ElevenLabs voices and exit')
    parser.add_argument('--voice-stability', type=float, default=float(os.getenv('VOICE_STABILITY', '0.71')),
                        help='Voice stability (0.0-1.0, default: 0.71)')
    parser.add_argument('--voice-clarity', type=float, default=float(os.getenv('VOICE_CLARITY', '0.75')),
                        help='Voice clarity/similarity (0.0-1.0, default: 0.75)')
    parser.add_argument('--voice-style', type=float, default=float(os.getenv('VOICE_STYLE', '0.5')),
                        help='Speaking style amount (0.0-1.0, default: 0.5)')
    
    args = parser.parse_args()
    
    # Check if required API keys are available
    if not args.nyt_api_key:
        print("Error: New York Times API key not provided. Set NYT_API_KEY environment variable or use --nyt-api-key")
        return
    
    if not args.claude_api_key:
        print("Error: Claude API key not provided. Set CLAUDE_API_KEY environment variable or use --claude-api-key")
        return
    
    # Voice agent is optional - only check if text-only mode is not enabled
    if not args.text_only and not args.eleven_api_key:
        print("Warning: ElevenLabs API key not provided. Running in text-only mode.")
        print("To enable voice, set ELEVEN_API_KEY environment variable or use --eleven-api-key")
        args.text_only = True
    
    # If just listing voices, do that and exit
    if args.list_voices and args.eleven_api_key:
        try:
            voice_agent = VoiceAgent(api_key=args.eleven_api_key)
            available_voices = voice_agent.get_available_voices()
            print("\nAvailable ElevenLabs Voices:")
            print("----------------------------")
            for voice in available_voices:
                print(f"Name: {voice['name']}")
                print(f"ID: {voice['id']}")
                print("----------------------------")
            return
        except Exception as e:
            print(f"Error listing voices: {e}")
            return
    
    # Get all articles using NYT API
    print("Fetching articles...")
    news_data = get_all_articles(args.nyt_api_key)
    
    # Initialize analyzer
    print("Analyzing articles...")
    analyzer = NewsAnalyzer(api_key=args.claude_api_key)
    
    # Run analysis
    analysis = analyzer.analyze_news_data(news_data)
    
    # Generate report
    print("\nGenerating report...\n")
    report = analyzer.generate_summary_report(analysis)
    
    # Print report
    print(report)
    
    # If not in text-only mode, use voice agent to read the report
    if not args.text_only:
        try:
            print("\nInitializing voice agent...")
            voice_agent = VoiceAgent(
                api_key=args.eleven_api_key, 
                voice_id=args.eleven_voice_id,
                voice_name=args.voice_name,
                stability=args.voice_stability,
                clarity=args.voice_clarity,
                style=args.voice_style
            )
            
            # Set user name for personalization
            if args.user_name:
                voice_agent.set_user_name(args.user_name)
            
            # Extract headlines from all sections with their section names
            all_headlines = []
            all_sections = []
            
            for section, data in analysis['sections'].items():
                headlines = data.get('recent_headlines', [])
                # Take only the first few headlines from each section
                for headline in headlines[:3]:
                    all_headlines.append(headline)
                    all_sections.append(section.capitalize())
            
            print("\nReading headlines...")
            voice_agent.read_headlines(all_headlines, all_sections)
            
            # Ask user if they want to hear the full report
            user_input = input("\nWould you like to hear the full report? (y/n): ")
            if user_input.lower() in ['y', 'yes']:
                print("\nReading full report...")
                voice_agent.read_summary(report)
        
        except Exception as e:
            print(f"Error with voice synthesis: {e}")
            print("Continuing in text-only mode.")
    
if __name__ == "__main__":
    main()