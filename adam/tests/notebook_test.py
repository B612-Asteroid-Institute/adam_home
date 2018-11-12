import subprocess
import tempfile
import nbformat
import os


# https://blog.thedataincubator.com/2016/06/testing-jupyter-notebooks/
def _process_notebook(path):
    '''
        Execute a jupyter notebook via nbconvert and collect the output.

        returns:    parsed nb object
                    execution errors
    '''
    # convert *.ipynb from jupyter notebook to py notebook
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
        args = ["jupyter", "nbconvert",
                "--to", "notebook", "--execute",
                "--ExecutePreprocessor.timeout=120",
                "--ExecutePreprocessor.kernel_name=python3",
                "--output", os.getcwd() + "/temp", path]
        # submodule allows you to spawn new processes, connect to their input/
        # output/error pipes, and obtain their return codes.
        subprocess.check_call(args)
        # seek() sets the file's current position.
        fout.seek(0)
        nb = nbformat.read(os.getcwd() + "/tempNB.ipynb", nbformat.current_nbformat)

    stream_type = [output for cell in nb.cells if "outputs" in cell
                   for output in cell["outputs"]
                   if output.output_type == "stream"]

    errors = 0
    for i in stream_type:
        make_str = str(i)
        # use doctest for unique string or set string message with unittest
        if '***Test Failed***' in make_str:
            errors = 1

    return nb, errors


def test():
    # initial CWD = adam_home
    print("cwd: ", os.getcwd())
    export PYTHONPATH = ${PYTHONPATH}: /home/travis/build/B612-Asteroid-Institute/adam_home
    # adam_home/demos
    notebook_path = os.getcwd() + '/demos/single_run_demo.ipynb'
    nb, errors = _process_notebook(notebook_path)

    # assert that errors is 0, otherwise fail
    assert errors == 0, 'Executed Notebook Returned with ERRORS'


def main():
    test()


if __name__ == "__main__":
    main()
