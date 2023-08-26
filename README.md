# Media Harmony

### Description.
A VideoUploader service based on FastAPI and swagger that supports uploading all kinds of video types,
uploads the content into AWS s3 and sends the s3 url throught rabbitmq to the VideoProcessor service which attaches
a background music to the desired video and stores the result in AWS S3.
once the user executes a valid request they should get a presigned URL link.

Note: The VideoProcessor service keeps the regular video sound at 80% volume and adds the background audio at 20% volume.
That way the user can still hear the video sound and the background music as a soft background.


### Installation.

1. Clone the repository.
2. Make sure you have AWS s3 bucket named panjaya
3. put your aws credentials in app/settings.toml and movie_maker/settings.toml
4. run: `docker-compose up'

### Usage.
Once you run the docker compose, you can access the api at http://localhost:8080/docs#/
Upload your video file and you will get the response with the video url in s3 bucket.

### Testing.
1. To run the test, run cd into the api/ and run `python -m tests/`
2. To run the test, run cd into the movie_maker/ and run `python -m tests/`