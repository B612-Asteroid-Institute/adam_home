from setuptools import setup

##
## Infer version from git tag information
##
def git_version():
      # Uses the following logic:
      #
      # * If the current commit has an annotated tags, the version is simply the tag with
      #   the leading 'v' removed.
      #
      # * If the current commit is past an annotated tag, the version is constructed at:
      #
      #    '{tag}.dev{commitcount}+{gitsha}'
      #
      #  where {commitcount} is the number of commits after the tag (obtained with `git describe`)
      #
      # * If there are no annotated tags in the past, the version is:
      #
      #    '0.0.0.dev{commitcount}+{gitsha}'
      #
      # Inspired by https://github.com/pyfidelity/setuptools-git-version
      # Creates PEP-440 compliant versions

      from subprocess import check_output

      command = 'git describe --tags --long --dirty --always'
      version = check_output(command.split()).decode('utf-8').strip()

      parts = version.split('-')
      if len(parts) in (3, 4):
            dirty = len(parts) == 4
            tag, count, sha = parts[:3]
            if not tag.startswith('v'):
                  raise Exception("Annotated tags on the repository must begin with the letter 'v'. Please fix this then try building agains.")
            tag = tag[1:]
            if count == '0' and not dirty:
                  return tag
      elif len(parts) in (1, 2):
            tag = "0.0.0"
            dirty = len(parts) == 2
            sha = parts[0]
            # Number of commits since the beginning of the current branch
            count = check_output("git rev-list --count HEAD".split()).decode('utf-8').strip()

      fmt = '{tag}.dev{commitcount}+{gitsha}'
      return fmt.format(tag=tag, commitcount=count, gitsha=sha.lstrip('g'))

setup(name="adam",
      version=git_version(),
      author="ADAM Developers",
      description="Asteroid Detection, Analysis, and Mapping (ADAM) Client",
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      url="https://github.com/B612-Asteroid-Institute/adam_home",
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD License",
            "Development Status :: 3 - Alpha",
            "Operating System :: POSIX :: Linux",
            "Operating System :: MacOS :: MacOS X"
      ],
      install_requires=['requests', 'pandas'],
      packages=['adam', 'adam.stk'],
      entry_points = {
            'console_scripts': ['adamctl=adam.__main__:main'],
      }
      )
