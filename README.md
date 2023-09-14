# Media Harmony

## Description.
A VideoUploader service based on FastAPI and swagger that supports uploading all kinds of video types,
uploads the content into AWS s3 and sends the s3 url through rabbitmq to the VideoProcessor service which attaches
a background music to the desired video and stores the result in AWS S3.
once the user executes a valid request they should get a pre-signed URL link.

Note: The VideoProcessor service keeps the regular video sound at 80% volume and adds the background audio at 20% volume.
That way the user can still hear the video sound and the background music as a soft background.


## Installation.

1. Clone the repository.
2. Make sure you have AWS s3 bucket named media-harmony
3. put your aws credentials in app/settings.toml and movie_maker/settings.toml


## Usage.
Once you run the docker compose, you can access the api at http://localhost:8080/docs#/
Upload your video file and you will get the response with the video url in s3 bucket.

## Testing.
1. To run the test, run cd into the api/ and run `python -m pytest tests/`
2. To run the test, run cd into the movie_maker/ and run `python -m pytest tests/`



## Deployment options
### On local machine
#### Using docker-compose
   run: `docker-compose up`
#### using docker
   build:
   `cd movie_maker/`
   `docker build -t mediaharmony-movie_maker .`
   `cd api/`
   `docker build -t mediaharmony-api .`
   rabbitmq: `docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 --network my_network rabbitmq:management`
   api: `docker run -d --name mediaharmony-api -p 8080:5000 --network my_network mediaharmony-api sh -c "sleep 10 && python routes.py"`
   movie_maker: `docker run -d --name mediaharmony-movie_maker --network my_network mediaharmony-movie_maker sh -c "sleep 10 && python messaging_system/video_queue.py"`
