FROM public.ecr.aws/lambda/python:3.9

# Install the function's dependencies using file requirements.txt
# from your project folder.
COPY requirements.txt  .
# Install dependencies
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN python3 -m nltk.downloader punkt -d "${LAMBDA_TASK_ROOT}/nltk_data"

# Copy all files of the function code to the image
COPY /. ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "main.handler" ]