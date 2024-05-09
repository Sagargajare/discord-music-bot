# Use an official Python image as the base
FROM ubuntu:latest

FROM python:3.8

# Set the working directory
WORKDIR /app

# Copy requirements to the working directory
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install -r requirements.txt

# Install FFmpeg, Chrome, ChromeDriver, and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg wget gnupg unzip curl software-properties-common

# Install the Opus library
RUN apt-get update && apt-get install -y libopus-dev

# Copy the entire application to the working directory
COPY . /app

# Install the `python-dotenv` package to read the .env file
RUN pip install python-dotenv

RUN pip install youtube-search-python

RUN pip install git+https://github.com/ytdl-org/youtube-dl.git@master#egg=youtube_dl
# Expose any ports used by the application
EXPOSE 8080

# Command to run the Python application
CMD ["python", "bot.py"]
