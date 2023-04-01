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

        # Get the count of tokens for each every caption
        print('Counting tokens in captions...')
        captions = [caption['text'] for caption in transcript]
        token_counts = list(map(self._count_tokens, captions))

        # Creates chunks of captions based on the token count
        print('Creating chunks of captions...')
        captions = list(zip(captions, token_counts))
        chunks = self._create_chunks(captions)

        # Generate prompts from chunks
        print('Generating prompts...')
        prompts = list(map(self._gen_prompt, chunks))
        print(len(prompts)) # Should be one

        # Create chat completions from prompts
        print('Creating chat completions...')
        chat_completions = list(map(self._chat_completion, prompts))

        # Amend chat completions
        print('Amending chat completions...')
        amended_chat_completions = self._amend_completions(chat_completions)

        # Parse the chat completion
        print('Parsing chat completions...')
        enriched_transcript = self._parse_chat_completion(amended_chat_completions)

        # Interpolate timestamps for the enriched transcript,
        # based on the original transcript postions and timestamps
        print('Interpolating timestamps...')
        pos_timestamps = self._get_pos_timestamps(transcript)
        interpolator = PositionInterpolator(pos_timestamps)
        for cap in enriched_transcript:
            cap['start'] = interpolator.interpolate(cap['position'])

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
    
    def _chat_completion(self, text):

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
        print('Requesting chat completion...')
        for i in range(10):
            response = requests.post(url, headers=headers, json = body)

            if response.status_code == 429 or response.status_code == 500:
                time.sleep(backoff_time)
                backoff_time *= 2
            else:
                break
        
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    def _amend_completions(self, completions: list):
        amended_completion = ''
        start_char = '\n'
        for completion in completions:
            # Strip
            completion = completion.strip()
            # Check for [INCOMPLETE] tags at the beginning end of the completion
            if completion.startswith('[INCOMPLETE]'):
                completion = completion[12:].strip()
            
            amended_completion += start_char + completion
            # Check for the [INCOMPLETE] tag at the end
            if amended_completion.endswith('[INCOMPLETE]'):
                amended_completion = amended_completion[:-12].strip()
                start_char = ' '
            else:
                start_char = '\n'

        return '\n' + amended_completion
    
    def _parse_completion(self, completion: str):
        completion_lines = completion.splitlines()
        transcript = []
        pos = 0
        for line in completion_lines:
            transcript.append({'text': line, 'start': None, 'position': pos})
            pos += len(line) + 1
        return transcript
    
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