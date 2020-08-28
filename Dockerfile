FROM continuumio/miniconda3:latest

RUN mkdir /src
WORKDIR /src

RUN conda update conda

COPY . .

RUN conda create -n adam-dev --file conda-requirements.txt \
  && conda init bash \
  && . /root/.bashrc \
  && conda activate adam-dev \
  && python setup.py develop \
  && adamctl login \
  && adamctl login dev https://adam-dev-193118.appspot.com/_ah/api/adam/v1 \
  && adamctl config envs.prod.workspace "$UUID" \
  && adamctl config envs.dev.workspace "$UUID" 

ENV PATH $PATH

CMD jupyter nbconvert --to python $NOTEBOOK