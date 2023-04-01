aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin 358737600086.dkr.ecr.us-east-1.amazonaws.com
sudo docker build -t yt-guesser-dev-transcript-processor src/process_transcripts/.
sudo docker tag yt-guesser-dev-transcript-processor:latest 358737600086.dkr.ecr.us-east-1.amazonaws.com/yt-guesser-dev-transcript-processor:latest
sudo docker push 358737600086.dkr.ecr.us-east-1.amazonaws.com/yt-guesser-dev-transcript-processor:latest