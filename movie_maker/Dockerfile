FROM python:3.9


RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /movie_maker

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

# Add the project directory to the PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/movie_maker"


CMD ["python", "messaging_system/video_queue.py"]
