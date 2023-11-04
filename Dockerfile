FROM python:3.11

LABEL maintainer="Paul Philion <philion@seattlecommunitynetwork.com>"

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY ./*.py /
RUN chmod +x /threader.py

ENV PYTHONPATH=/

# run the job
CMD ["/threader.py"]