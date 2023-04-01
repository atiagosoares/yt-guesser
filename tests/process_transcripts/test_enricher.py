import sys
# Add the parent directory to the path so we can import the Enricher class
sys.path.append('src/process_transcripts')

import pytest
from enricher import OpenAIChatEnricher
import os
import json

OPENAI_API_KEY_PARAMETER_NAME = os.environ.get('OPENAI_API_KEY')
enricher = OpenAIChatEnricher(OPENAI_API_KEY_PARAMETER_NAME)

transcript_json = '''
[
    {"text": "so how many types of nerds are there out", "start": 0.01, "duration": 4.92},
    {"text": "there so I have a list you got developer", "start": 3.01, "duration": 5.52},
    {"text": "nerds you got audiophile nerds you have", "start": 4.93, "duration": 6.9},
    {"text": "gaming nerds you have bang Olu some", "start": 8.53, "duration": 5.04},
    {"text": "nerds those are a very specialized nerd", "start": 11.83, "duration": 4.86},
    {"text": "case anyway you got Tech Hardware nerds", "start": 13.57, "duration": 6.18},
    {"text": "you also have Star Wars nerds so what", "start": 16.69, "duration": 5.759},
    {"text": "other types of nerds are out there try", "start": 19.75, "duration": 4.92},
    {"text": "to think about the major branches of", "start": 22.449, "duration": 4.441},
    {"text": "nerdness not the specialized super nerds", "start": 24.67, "duration": 5.16},
    {"text": "but the major branches of nerdness let", "start": 26.89, "duration": 6.139},
    {"text": "me know in the comments below", "start": 29.83, "duration": 3.199}
]
'''
transcript = json.loads(transcript_json)

# Initialize object for testing
def test_concat_transcript():
    concat_transcript = enricher._concat_transcript(transcript)
    want = '''
so how many types of nerds are there out
there so I have a list you got developer
nerds you got audiophile nerds you have
gaming nerds you have bang Olu some
nerds those are a very specialized nerd
case anyway you got Tech Hardware nerds
you also have Star Wars nerds so what
other types of nerds are out there try
to think about the major branches of
nerdness not the specialized super nerds
but the major branches of nerdness let
me know in the comments below
'''
    assert concat_transcript == want
