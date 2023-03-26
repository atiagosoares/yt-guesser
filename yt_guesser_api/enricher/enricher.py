import os
import json
from nltk.tokenize import word_tokenize
import requests
import time

from .prompts import BasePrompt

class TranscriptEnricher():

    def __init__(self):
        self.transcript = transcript
    
    def enrich(self, transcript):
        pass

class OpenAPIChatEnricher(TranscriptEnricher):

    def __init__(self, transcript, api_key, model = "gpt-3.5-turbo"):
        self.transcript = transcript
        self.api_key = api_key
        self.base_prompt = BasePrompt
        self.model = model 

    def enrich(self, transcript):

        # Concatenate the transcript
        print('Creating the wall of text...')
        poor_wall = self._concat_transcript(transcript) # wall of text
        
        # Split the wall into chunks
        print('Creating chunks...')
        chunks = self._chunck_wall(poor_wall)
        
        # Enrich the the chunks
        print('Enriching the chunks...')
        enriched_chunks = [self._enrich_text(chunk) for chunk in chunks]
        
        # Concatenate the chunks
        print('Concatenating the chunks...')
        enriched_wall = ' '.join(enriched_chunks)


    def _concat_transcript(self, transcript):
        '''
        Concatenates the transcript into a single string (a wall of text)
        '''
        wall = ''
        for item in transcript:
            wall += item['text']
        return wall

    def _chunck_wall(self, wall, chunk_size = 1500):
        '''
        Splits the wall of text into chunks of a given size
        '''
        token_chunks = []

        # Tokenize the wall
        tokens = word_tokenize(self, wall)

        # Split the tokens into chunks
        for i in range(0, len(tokens), chunk_size):
            token_chunks.append(tokens[i:i + chunk_size])
        # Join the chunks back into a string
        chunks = [' '.join(chunk) for chunk in token_chunks]
        return chunks

    def _enrich_text(self, text):

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.api_key
        }
        messages = [
            {'role': 'user', 'content': self + prompt}
        ]
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        # Exponential backoff request
        backoff_time = 0.1
        for i in range(10):
            response = requests.post(url, headers=headers, json = body)

            if response.status_code == 429 or response.status_code == 500:
                time.sleep(backoff_time)
                backoff_time *= 2
            else:
                break
        
        response.raise_for_status()
        return response['choices'][0]['message']['content']