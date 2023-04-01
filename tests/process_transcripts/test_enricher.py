import sys
# Add the parent directory to the path so we can import the Enricher class
sys.path.append('src/process_transcripts')

import pytest
from enricher import OpenAIChatEnricher, PositionInterpolator
import os
import json

OPENAI_API_KEY_PARAMETER_NAME = os.environ.get('OPENAI_API_KEY')
enricher = OpenAIChatEnricher(OPENAI_API_KEY_PARAMETER_NAME)

transcript_json = '''
[
    {"text": "so how many types of nerds are there out", "start": 0.01, "duration": 4.92},
    {"text": "there so I have a list you got developer", "start": 3.01, "duration": 5.52},
    {"text": "nerds you got audiophile nerds you have", "start": 4.93, "duration": 6.9},
    {"text": "gaming nerds you have bang me", "start": 8.53, "duration": 5.04},
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

# ------------------------------------------------------- COUNT TOKENS -------------------------------------------------------
def test_count_tokens():
    # Shoudld return something like this:
    assert enricher._count_tokens(transcript[0]['text']) == 9
    assert enricher._count_tokens(transcript[1]['text']) == 9
    assert enricher._count_tokens(transcript[2]['text']) == 7

def test_count_tokens_map():
    # Should return something like this:
    captions = [caption['text'] for caption in transcript]
    token_counts = list(map(enricher._count_tokens, captions))
    assert token_counts == [len(caption.split(' ')) for caption in captions]

# ------------------------------------------------------- GET POS TIMESTAMPS --------------------------------------------------
'''
Assumptions about the transcript:
- 'start' is float and never null
- 'text' is string and never null
- There will be at least two captions
'''
def test_get_pos_timestamps_empty():
    # Edge case: empty caption
    # Should never happen, but behavior is defined, just in case
    captions = []
    timestamps = enricher._get_pos_timestamps(captions)
    assert timestamps == []

def test_get_pos_timestamps_single():
    # Single caption
    # Should never happen, but behavior is defined, just in case
    captions = [{'start': 0.00, 'text': 'foo'}]
    timestamps = enricher._get_pos_timestamps(captions)
    assert timestamps == [(0, 0.00)]

def test_get_pos_timestamps_multiple():
    # Multiple captions
    captions = [
        {'start': 0.00, 'text': 'foo'},
        {'start': 5.00, 'text': 'bar'},
        {'start': 10.00, 'text': 'baz'}
    ]
    timestamps = enricher._get_pos_timestamps(captions)
    assert timestamps == [(0, 0.00), (4, 5.00), (8, 10.00)]

# ------------------------------------------------------- CREATE CHUNKS -------------------------------------------------------
def test_create_chunks_empty_list():
    # Edge case: empty caption
    captions = []
    chunks = enricher._create_chunks(captions)
    assert chunks == [] # Empty list

def test_create_chunks_single():
    # Should split the strings in chunks of >=1500 tokens
    captions = [
        ('foo', 1000),
        ('bar', 499),
    ]
    chunks = enricher._create_chunks(captions)
    assert chunks == [['foo', 'bar']] # Single chunk

    captions = [
        ('foo', 1000),
        ('bar', 500)
    ]
    chunks = enricher._create_chunks(captions)
    assert chunks == [['foo', 'bar']] # Single chunk

def test_create_chunks_multiple():
    captions = [
        ('foo', 1000),
        ('bar', 501)
    ]
    chunks = enricher._create_chunks(captions)
    assert chunks == [['foo'], ['bar']] # Two chunks

def test_create_chunks_max_size():
    # Has a maximum size chunk
    captions = [
        ('foo', 1000),
        ('bar', 1500)
    ]
    chunks = enricher._create_chunks(captions)
    assert chunks == [['foo'], ['bar']] # Two chunks

def test_create_chunks_over_max_size():
    # Chunk over 1500 tokens
    captions = [('foo', 1501)]
    with pytest.raises(ValueError):
        enricher._create_chunks(captions)

# ------------------------------------------------------- GEN PROMPT -------------------------------------------------------
def test_gen_prompt_empty():
    # Edge case: empty caption
    prompt = enricher._gen_prompt([])
    assert prompt == ''

def test_gen_prompt_single():
    # Single caption
    prompt = enricher._gen_prompt(['foo'])
    assert prompt == '\nfoo'

def test_gen_prompt_multiple():
    # Multiple captions
    prompt = enricher._gen_prompt(['foo', 'bar'])
    assert prompt == '\nfoo\nbar'

# ------------------------------------------------------- CHAT COMPLETION -------------------------------------------------------
# Will not test because interacts with OpenAI API
# Will leave it to the will of the gods

# ------------------------------------------------------- AMEND COMPLETIONS ------------------------------------------------------
def test_amend_completions_00():
    completions = []
    want = '\n'
    assert enricher._amend_completions(completions) == want

def test_amend_completions_01():
    completions = ['\n Foo.', 'Bar [INCOMPLETE]', '[INCOMPLETE] baz. \n']
    want = '\nFoo.\nBar baz.'
    assert enricher._amend_completions(completions) == want
# ------------------------------------------------------- PARSE COMPLETION -------------------------------------------------------
def test_parse_completion_empty():
    # Edge case: empty caion
    completion = 'Foo.\nBar.\nBaz.\n'
    parsed_completion = enricher._parse_completion(completion)
    assert parsed_completion == [
        {'text': 'Foo.', 'start': None, 'position': 0},
        {'text': 'Bar.', 'start': None, 'position': 5},
        {'text': 'Baz.', 'start': None, 'position': 10}
    ]

# ------------------------------------------------------- Interpolator -------------------------------------------------------
positions = [(0, 0.00), (5, 6.00), (10, 9.00)]
interpolator = PositionInterpolator(positions)

def test_interpolate_defined():
    # Edge case: interpolationpoints matches curve points
    assert interpolator.interpolate(0) == 0.00
    assert interpolator.interpolate(5) == 6.00
    assert interpolator.interpolate(10) == 9.00

def test_interpolate_inside():
    # Edge case: interpolationpoints does not match curve points
    assert interpolator.interpolate(1) == 1.20
    assert interpolator.interpolate(2) == 2.40
    assert interpolator.interpolate(3) == 3.60
    assert interpolator.interpolate(4) == 4.80

    assert interpolator.interpolate(6) == 6.6
    assert interpolator.interpolate(7) == 7.2
    assert interpolator.interpolate(8) == 7.8
    assert interpolator.interpolate(9) == 8.4

def test_interpolate_outside():
    # Edge case: interpolationpoints outside curve points
    assert interpolator.interpolate(-1) == -1.2
    assert interpolator.interpolate(11) == 9.6

# ------------------------------------------------------- INTEGRATION TEST -------------------------------------------------------
# Uncomment and run manually with pytest

# def test_enrich():
#     # Must run without errors
#     enriched_transcript = enricher.enrich(transcript)
#     for cap in enriched_transcript:
#         print(f"{cap['start']}: {cap['text']}")