# Remove existing build artifacts
rm -rf build/process_transcripts/*
# Install dependencies
pip install -r src/process_transcripts/requirements.txt -t build/process_transcripts
# Move source code
# Activate the environment and install nltk punkt
python -m nltk.downloader punkt -d build/process_transcripts/nltk_data
cp -r src/process_transcripts/* build/process_transcripts