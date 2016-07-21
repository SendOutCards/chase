FROM python:2.7.12
ADD . /code/
WORKDIR /code
RUN echo 'set editing-mode vi' >> /etc/inputrc ;\
    python setup.py build && python setup.py install && pip install ipython
