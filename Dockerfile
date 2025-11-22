#Step 1: Use python base image
FROM python:3.12-slim

#Step 2: define a working directory for the container
WORKDIR /app

#STep 3: Copy the requirements into container
COPY requirements.txt .

#step 4: Install the dependencies on the container
RUN pip install -r requirements.txt

#Step 5: Copy the flask application into the container
COPY . .

#Step 6: Expose a port
EXPOSE 5000

#Step 7: Setting flask env vars
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

#STep 8: Run flask app
CMD ["flask", "run"]