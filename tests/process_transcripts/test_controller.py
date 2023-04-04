import sys
# Add the parent directory to the path so we can import the Enricher class
sys.path.append('src/process_transcripts')

import pytest
import json
from main import Controller
from enricher.enricher import MockEnricher

# Load test data
with open('tests/test_events/brain_waves.json') as f:
    brain_waves_event = json.load(f)

