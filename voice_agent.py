from elevenlabs import generate, play, set_api_key, voices, Voice, save
from elevenlabs.api import History
import time
import tempfile
import os
import pygame
from typing import List, Dict, Optional
import random

class VoiceAgent:
    def __init__(self, api_key: str, voice_id: Optional[str] = None, 
                 voice_name: Optional[str] = None,
                 stability: float = 0.71, 
                 clarity: float = 0.75,
                 style: float = 0.0):
        """
        Initialize the Voice Agent with ElevenLabs.
        
        Args:
            api_key (str): ElevenLabs API key
            voice_id (str, optional): Specific voice ID to use
            voice_name (str, optional): Name of voice to use (will search for matching voice)
            stability (float): Voice stability (0.0-1.0)
            clarity (float): Voice clarity/similarity (0.0-1.0)
            style (float): Speaking style (0.0-1.0)
        """
        set_api_key(api_key)
        self.stability = stability
        self.clarity = clarity
        self.style = style
        self.voice_id = voice_id
        self.user_name = "News Listener"
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Get available voices
        self.available_voices = voices()
        
        # If voice name is provided, try to find matching voice
        if voice_name and not voice_id:
            for voice in self.available_voices:
                if voice_name.lower() in voice.name.lower():
                    self.voice_id = voice.voice_id
                    break
        
        # If no voice_id set yet, use the first available voice
        if not self.voice_id and self.available_voices:
            self.voice_id = self.available_voices[0].voice_id
        
        if not self.voice_id:
            raise ValueError("No voices available in your ElevenLabs account")
            
        # Get the voice name for display
        self.voice_name = self._get_voice_name()
    
    def _get_voice_name(self) -> str:
        """Get the name of the current voice"""
        for voice in self.available_voices:
            if voice.voice_id == self.voice_id:
                return voice.name
        return "Unknown Voice"
    
    def set_user_name(self, name: str) -> None:
        """Set the user's name for personalization"""
        self.user_name = name
    
    def read_text(self, text: str) -> None:
        """
        Read text aloud using ElevenLabs TTS with configured voice settings.
        
        Args:
            text (str): Text to be read aloud
        """
        try:
            voice_settings = Voice(
                voice_id=self.voice_id,
                settings={
                    "stability": self.stability,
                    "similarity_boost": self.clarity,
                    "style": self.style,
                    "use_speaker_boost": True
                }
            )
            
            audio = generate(
                text=text,
                voice=voice_settings,
                model="eleven_multilingual_v2"
            )
            
            # Play the audio
            play(audio)
        except Exception as e:
            print(f"Error generating speech: {e}")
            
    def generate_audio(self, text: str):
        """
        Generate audio for text using ElevenLabs TTS without playing it.
        
        Args:
            text (str): Text to convert to speech
            
        Returns:
            bytes: Audio data
        """
        try:
            voice_settings = Voice(
                voice_id=self.voice_id,
                settings={
                    "stability": self.stability,
                    "similarity_boost": self.clarity,
                    "style": self.style,
                    "use_speaker_boost": True
                }
            )
            
            audio = generate(
                text=text,
                voice=voice_settings,
                model="eleven_multilingual_v2"
            )
            
            return audio
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    def get_greeting(self) -> str:
        """Generate a personalized greeting based on time of day"""
        import datetime
        
        current_hour = datetime.datetime.now().hour
        greeting = "Good morning" if 5 <= current_hour < 12 else "Good afternoon" if 12 <= current_hour < 18 else "Good evening"
        
        greetings = [
            f"{greeting}, {self.user_name}! Here's your news briefing.",
            f"Welcome to your personalized news briefing, {self.user_name}!",
            f"{greeting}! I've gathered the latest headlines just for you, {self.user_name}.",
            f"Hello {self.user_name}! It's {greeting.lower()} and I have your news briefing ready."
        ]
        
        return random.choice(greetings)
    
    def read_headlines(self, headlines: List[str], sections: Optional[List[str]] = None) -> None:
        """
        Read a list of headlines with a brief pause between each, grouped by section if provided.
        
        Args:
            headlines (List[str]): List of headlines to read
            sections (List[str], optional): List of section names corresponding to headlines
        """
        try:
            # Read personalized introduction
            intro = self.get_greeting()
            self.read_text(intro)
            time.sleep(0.4)  # Reduced pause
            
            self.read_text("Here are today's top headlines:")
            time.sleep(0.4)  # Reduced pause
            
            # Read each headline with a shorter pause between
            if sections and len(sections) == len(headlines):
                # Group by sections
                section_grouped = {}
                for i, headline in enumerate(headlines):
                    section = sections[i]
                    if section not in section_grouped:
                        section_grouped[section] = []
                    section_grouped[section].append(headline)
                
                # Read headlines by section
                for section, section_headlines in section_grouped.items():
                    self.read_text(f"From {section}:")
                    time.sleep(0.3)  # Reduced pause after section announcement
                    
                    for i, headline in enumerate(section_headlines):
                        transition_phrases = ["", "Next up: ", "Also in the news: ", "Another headline: "]
                        prefix = random.choice(transition_phrases) if i > 0 else ""
                        self.read_text(f"{prefix}{headline}")
                        time.sleep(0.3)  # Reduced pause between headlines
                    
                    time.sleep(0.5)  # Reduced pause between sections
            else:
                # Read headlines without section grouping
                for i, headline in enumerate(headlines):
                    transition_phrases = ["", "Next: ", "Also: ", "Moving on: "]
                    prefix = random.choice(transition_phrases) if i > 0 else ""
                    self.read_text(f"{prefix}{headline}")
                    time.sleep(0.3)  # Reduced pause between headlines
            
            # Closing statement
            self.read_text("That concludes today's headlines.")
            
        except Exception as e:
            print(f"Error reading headlines: {e}")
    
    def read_summary(self, summary: str) -> None:
        """
        Read a full news summary, breaking it into manageable chunks.
        
        Args:
            summary (str): The full summary text to read
        """
        try:
            # Read introduction
            self.read_text("Here's your in-depth news analysis and summary:")
            time.sleep(0.5)  # Reduced pause
            
            # Split into paragraphs and organize by section headers
            sections = []
            current_section = {"title": "", "content": []}
            
            for line in summary.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a section header (numbered or all caps)
                if line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.isupper():
                    # Save previous section if it has content
                    if current_section["content"]:
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {"title": line, "content": []}
                else:
                    current_section["content"].append(line)
            
            # Add the last section
            if current_section["content"]:
                sections.append(current_section)
            
            # Read each section with faster pacing
            for section in sections:
                # Announce section with slight emphasis
                self.read_text(section["title"])
                time.sleep(0.4)  # Reduced pause after section title
                
                # Read content
                for paragraph in section["content"]:
                    self.read_text(paragraph)
                    time.sleep(0.3)  # Reduced pause between paragraphs
                
                time.sleep(0.5)  # Reduced pause between sections
            
            # Conclusion
            conclusions = [
                "That's all for today's news summary.",
                f"Thanks for listening, {self.user_name}. This concludes your news briefing.",
                "That's the end of your personalized news summary. Have a great day!",
                "This concludes today's news analysis. Until next time!"
            ]
            self.read_text(random.choice(conclusions))
            
        except Exception as e:
            print(f"Error reading summary: {e}")
    
    def get_available_voices(self) -> List[Dict]:
        """
        Get a list of available voices from ElevenLabs.
        
        Returns:
            List[Dict]: List of available voices with their details
        """
        try:
            available_voices = voices()
            return [{"name": voice.name, "id": voice.voice_id} for voice in available_voices]
        except Exception as e:
            print(f"Error getting voices: {e}")
            return []