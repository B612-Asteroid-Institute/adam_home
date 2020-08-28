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
  && echo "export CONDA_DEFAULT_ENV='adam-dev' \n\
  export CONDA_EXE='/opt/conda/bin/conda' \n\
  export CONDA_PREFIX='/opt/conda/envs/adam-dev' \n\
  export CONDA_PREFIX_1='/opt/conda' \n\
  export CONDA_PROMPT_MODIFIER='(adam-dev) ' \n\
  export CONDA_PYTHON_EXE='/opt/conda/bin/python' \n\
  export CONDA_SHLVL='2' \n\
  export PATH='/opt/conda/envs/adam-dev/bin:/opt/conda/condabin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' \
  " >> /src/.bashrc

CMD . /src/.bashrc && adamctl login \
  && adamctl login dev https://adam-dev-193118.appspot.com/_ah/api/adam/v1 \
  && adamctl config envs.prod.workspace "$UUID" \
  && adamctl config envs.dev.workspace "$UUID" \
  jupyter nbconvert --to python $NOTEBOOK