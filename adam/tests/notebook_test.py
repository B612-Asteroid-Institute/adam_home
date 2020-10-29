import subprocess
import tempfile
import nbformat
import os
import os.path
import pytest


# https://blog.thedataincubator.com/2016/06/testing-jupyter-notebooks/
def _process_notebook(path):
    '''
        Execute a jupyter notebook via nbconvert and collect the output.

        returns:    parsed nb object
                    execution errors
    '''
    # convert *.ipynb from jupyter notebook to py notebook
    with tempfile.TemporaryDirectory() as tmpdir:
        outnbfn = os.path.join(tmpdir, "out.ipynb")
        args = ["jupyter", "nbconvert",
                "--to", "notebook", "--execute",
                "--ExecutePreprocessor.timeout=120",
                "--ExecutePreprocessor.kernel_name=python3",
                "--output", outnbfn, path]
        subprocess.check_call(args)
        nb = nbformat.read(outnbfn, nbformat.current_nbformat)

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


@pytest.mark.skip("Set up integration test environment and run notebook against it")
@pytest.mark.notebook
def test():
    notebook_path = os.path.dirname(__file__) + '/../../demos/single_run_demo.ipynb'
    nb, errors = _process_notebook(notebook_path)

    # assert that errors is 0, otherwise fail
    assert errors == 0, 'Executed Notebook Returned with ERRORS'


def main():
    test()


if __name__ == "__main__":
    main()
