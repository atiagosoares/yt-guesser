# Remove existing build artifacts
rm -rf build/process_transcripts/*
# Install dependencies
pip install -r src/process_transcripts/requirements.txt -t build/process_transcripts
# Move source code
cp -r src/process_transcripts/* build/process_transcripts