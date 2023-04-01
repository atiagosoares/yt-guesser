import os
import json
import nltk
from nltk.tokenize import word_tokenize
import requests
import time
from helpers import ApproximateMap, TextFinder

from .prompts import BasePrompt

class TranscriptEnricher():

    def __init__(self):
        pass
    
    def enrich(self, transcript):
        pass

class OpenAIChatEnricher(TranscriptEnricher):

    def __init__(self, api_key, model = "gpt-3.5-turbo"):
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
        enriched_wall = self._join_chunks(chunks)

        # Find the positon for the transcript entries
        transcript_positions = self._find_transcript_positions(enriched_wall, transcript)
        # Create map of position -> timestamp
        position_timestamps = ApproximateMap()
        for pos, ts in zip(transcript_positions, [item['start'] for item in transcript]):
            # Exlude cases where the position is None
            if pos:
                position_timestamps.add(pos, ts)

        # Recompose the enriched wall into a transcript
        enriched_transcript = self._recompose_transcript(enriched_wall, position_timestamps)

        return enriched_transcript


    def _concat_transcript(self, transcript):
        '''
        Concatenates the transcript into a single string (a wall of text)
        '''
        wall = ''
        for item in transcript:
            wall += '\n' + item['text']
        wall += '\n'
        
        return wall

    def _chunck_wall(self, wall, chunk_size = 1500):
        '''
        Splits the wall of text into chunks of a given size
        '''
        token_chunks = []

        # Tokenize the wall
        tokens = word_tokenize(wall)

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
            {'role': 'user', 'content': self.base_prompt + text}
        ]
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0
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
        return response.json()['choices'][0]['message']['content']
    
    def _join_chunks(self, chunks):
        '''
        Concatenates the chunks into a single string
        '''
        wall = ''
        for chunk in chunks:
            # Remove [INCOMPLETE] annotations from the begginging and end of the chunk
            chunk = chunk.replace('[INCOMPLETE]', '')
            # Remove the '- ' annotation from the beggining of every line
            chunk = chunk.replace('\n- ', '\n')
            wall += chunk
        return wall
    
    def _find_transcript_positions(self, wall, transcript):
        '''
        Find the positions of the transcript entries in the wall of text
        '''
        positions = []
        for item in transcript:
            positions.append(TextFinder().find_text(wall, item['text']))
        return positions
    
    def _recompose_transcript(self, wall, position_timestamps, start_safe_margin_ms = 1500):
        '''
        Recomposes the enriched wall into a transcript
        '''

        enriched_transcript = []
        entries = wall.splitlines()

        entry_pos = 0
        lower_bound = position_timestamps.get_lteq(entry_pos)
        upper_bound = position_timestamps.get_gt(entry_pos)
    
        for entry in entries:
            t_entry = {
                'text': entry
            }

            # Update bounds
            if upper_bound:
                if entry_pos >= upper_bound[0]:
                    lower_bound = upper_bound
                    upper_bound = position_timestamps.get_gteq(entry_pos)

            # Interpolate the start timestamp
            start_estimate = interpolate_value(lower_bound[0], upper_bound[0], lower_bound[1], upper_bound[1], entry_pos)
            t_entry['start'] = int(start_estimate*1000) - start_safe_margin_ms

            # Interpolate the end timestamp
            if entry_pos + len(entry) >= upper_bound[0]:
                entry_pos += len(entry)

        return enriched_transcript
    
def interpolate_value(a, c, fa, fc, b):
    '''
    Interpolates a value between two timestamps
    '''
    d = (fc - fa) / (c - a)
    return fa + d * (b - a)
        