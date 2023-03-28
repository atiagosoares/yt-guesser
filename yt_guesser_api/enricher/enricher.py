import os
import json
from nltk.tokenize import word_tokenize
import requests
import time

from .prompts import BasePrompt

class TranscriptEnricher():

    def __init__(self):
        pass
    
    def enrich(self, transcript):
        pass

class OpenAPIChatEnricher(TranscriptEnricher):

    def __init__(self, api_key, text_finder, model = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.base_prompt = BasePrompt
        self.model = model 
        self.text_finder = text_finder

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
        position_timestamps = {}
        for pos, ts in zip(transcript_positions, [item['timestamp'] for item in transcript]):
            # Exlude cases where the timestamp is None

        # Filter out the positions that don't have a position or timestamp
        position_timestamps = [item for item in position_timestamps if item[0] and item[1]]
        # Make sure positions are in order
        position_timestamps.sort(key = lambda item: item[0])

        # Recompose the enriched wall into a transcript
        enriched_transcript = self._recompose_transcript(enriched_wall, position_timestamps)


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
            {'role': 'user', 'content': self + text}
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
        return response['choices'][0]['message']['content']
    
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
            positions.append(self.text_finder.find_text(wall, item['text']))
        return positions
    
    def _recompose_transcript(self, wall, position_timestamps, start_safe_margin_ms = 1500):
        '''
        Recomposes the enriched wall into a transcript
        '''

        lower_idx = 0
        upper_idx = 1

        lower_pos, lower_ts = position_timestamps[lower_idx]
        upper_pos, upper_ts = position_timestamps[upper_idx]

        enriched_transcript = []
        entries = wall.splitlines()
        entry_pos = 0
        for entry in entries:
            t_entry = {
                'text': entry
            }

            # Interpoloate the start timestamp
            if entry_pos >= upper_pos:
                while upper_pos <= entry_pos or upper_pos is None:
                    upper_idx += 1
                    upper_pos, upper_ts = position_timestamps[upper_idx]

            start_estimate = self.interpolate_value(lower_pos, upper_pos, lower_ts, upper_ts, entry_pos)
            t_entry['start'] = start_estimate - start_safe_margin_ms

            # Interpolate the end timestamp
            if entry_pos + len(entry) >= upper_pos:
            entry_pos += len(entry)


        return enriched_transcript
    
    def _find_position_bounds(position, position_timestamps, init_idx = 0):
        '''
        Find the lower and upper bounds of a position in a list of position_timestamps

        We can assume that
        - the position_timestamps array is sorted by position AND timestamp
        - There are no null values
        '''


    
def interpolate_value(self, a, c, fa, fc, b):
    '''
    Interpolates a value between two timestamps
    '''
    d = (fc - fa) / (c - a)
    return fa + d * (b - a)
        