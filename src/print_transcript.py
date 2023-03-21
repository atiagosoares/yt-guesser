import json
import sys
from time import sleep

def main():
    transcript_name = sys.argv[1]

    # Load the transcript
    with open(f'data/{transcript_name}', 'r') as f:
        transcript = json.load(f)

    for phrase in transcript:
        start = int(phrase['start']*1000)
        print(f'{start:09d} {phrase["text"]}')

if __name__ == '__main__':
    main()
