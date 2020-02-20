ARG BASE_TAG=latest
FROM apluslms/grading-base:$BASE_TAG

RUN apt_install \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-wheel \
 && ln -s /usr/bin/python3 /usr/local/bin/python \
 && ln -s /usr/bin/pip3 /usr/local/bin/pip \
\
 && pip3 install --no-cache-dir --disable-pip-version-check html5lib tinycss pyjsparser \
 && find /usr/local/lib/python* -type d -regex '.*/locale/[a-z_A-Z]+' -not -regex '.*/\(en\|fi\|sv\)' -print0 | xargs -0 rm -rf \
 && find /usr/local/lib/python* -type d -name 'tests' -print0 | xargs -0 rm -rf

COPY python /usr/local/grade-web-python
ENV PYTHONPATH="/usr/local/grade-web-python:${PYTHONPATH}"
CMD ["/exercise/run.sh"]
