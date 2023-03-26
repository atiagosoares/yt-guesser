import json
import gc

def main():
    
    # Load the caption file
    print('Loading transcript...')
    with open('data/sample_transcript.json', 'r') as f:
        transcript = json.load(f)

    print('Coalescing transcript...')
    c_transcript = coalesce_transcript(transcript)
    
    # Save the results
    print('Saving results...')
    with open('data/sample_coalesced_script.json', 'w') as g:
        json.dump(c_transcript, g)
    print('Done!')

def coalesce_transcript(transcript):
    phrases = []
    new_buffer = {"text": "", "start": 0.0, "duration": 0.0}
    buffer = new_buffer.copy()

    for item in transcript:
        
        # If this item start with "-", start a new phrase
        if item['text'].startswith('-'):
            if len(buffer["text"]) > 0:
                phrases.append(buffer.copy())
                buffer = new_buffer.copy()
                buffer['start'] = item['start']
                gc.collect()

        # Append content
        buffer['text'] += ' ' + item['text']
        buffer['duration'] += item['duration']

    # Save the last buffer to the list of phrases
    phrases.append(buffer.copy())
    return phrases

if __name__ == "__main__":
    main()
