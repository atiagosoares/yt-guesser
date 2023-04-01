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

    def enrich(self, transcript: list):

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

    def _count_tokens(self, text: str):
        tokens = word_tokenize(text)
        return len(tokens)
    
    def _get_pos_timestamps(self, transcription: list):
        pos_timestamps = []
        cur_pos = 0
        for caption in transcription:
            pos_timestamps.append((cur_pos, caption['start']))
            cur_pos += len(caption['text']) + 1
        return pos_timestamps
    
    def _create_chunks(self, captions):
        chunks = []
        chunk_size = 0
        cur_chunk = []
        for cap in captions:
            if cap[1] > 1500:
                raise(ValueError('Transcription has a caption over 1500 tokens'))
            if chunk_size + cap[1] > 1500:
                # Create a new chunk
                chunks.append(cur_chunk)
                cur_chunk = []
            cur_chunk.append(cap[0])
            chunk_size += cap[1]

        # Append the last chunk
        if cur_chunk != []:
            chunks.append(cur_chunk)

        return chunks
    
    def _gen_prompt(self, captions: list):
        prompt = ''
        for cap in captions:
            prompt += '\n' + cap
        return prompt
    
class PositionInterpolator():
    def __init__(self, positions_ts: list):
        # Sort by position
        positions_ts.sort(key = lambda x: x[0])
        self.positions_ts = positions_ts
    
    def interpolate(self, p):
        # Find the closest two points to p
        a, b = self.positions_ts[:2]
        dist = abs(a[0] + b[0] -2*p)
        for i in range(3, len(self.positions_ts) + 1):
            temp_a, temp_b = self.positions_ts[i-2:i]
            temp_dist = abs(temp_a[0] + temp_b[0] - 2*p)
            if temp_dist >= dist:
                break 
            a, b, dist = temp_a, temp_b, temp_dist
        # Interpolate
        return a[1] + (p - a[0])*(b[1] - a[1])/(b[0] - a[0])