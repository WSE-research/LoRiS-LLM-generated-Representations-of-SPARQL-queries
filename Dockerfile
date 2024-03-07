FROM ubuntu:22.04

# parameters that might be provided at runtime by using the --env option
ENV REPLACE_INDEX_HTML_CONTENT="false"
ENV SERVER_PORT=8501
ENV CANONICAL_URL=""
ENV ADDITIONAL_HTML_HEAD_CONTENT=""
ENV BACKEND_URL=""

# install dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq bash curl wget ca-certificates python3 python3-pip 

# copy the application files
COPY . /app
WORKDIR /app

# install python dependencies
RUN python3 --version
RUN python3 -m pip install --upgrade pip 
RUN python3 -m pip install -r requirements.txt

# set environment variables for the required colorization of the terminal
ENV force_color_prompt=yes
ENV COLORTERM=24bit

# set environment variables for the application
ENV UPLOAD_DIRECTORY=/app/working_directory

# do a dry run to see if the applications would starts (so, we are not surprised if it doesn't work during the real start of the container)
RUN (export DRY_RUN=True; export BACKEND_URL=$BACKEND_URL; streamlit run loris--llm-based-explanations-for-sparql-queries.py &) && sleep 5 && curl http://localhost:${SERVER_PORT}/

EXPOSE $SERVER_PORT
HEALTHCHECK CMD curl --fail http://localhost:$SERVER_PORT/_stcore/health

# set all environment variables
ENTRYPOINT ["sh", "-c", "\
    export REPLACE_INDEX_HTML_CONTENT=$REPLACE_INDEX_HTML_CONTENT \
    export SERVER_PORT=$SERVER_PORT \
    export CANONICAL_URL=$CANONICAL_URL \
    export ADDITIONAL_HTML_HEAD_CONTENT=$ADDITIONAL_HTML_HEAD_CONTENT \
    export BACKEND_URL=$BACKEND_URL \
    && echo \"REPLACE_INDEX_HTML_CONTENT: $REPLACE_INDEX_HTML_CONTENT\" \
    && echo \"SERVER_PORT: $SERVER_PORT\" \
    && echo \"CANONICAL_URL: $CANONICAL_URL\" \
    && echo \"ADDITIONAL_HTML_HEAD_CONTENT: $ADDITIONAL_HTML_HEAD_CONTENT\" \
    && echo \"BACKEND_URL: $BACKEND_URL\" \
    && streamlit run loris--llm-based-explanations-for-sparql-queries.py --server.port=$SERVER_PORT --server.address=0.0.0.0 \
"]

