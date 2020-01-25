import sys

def main(args=None):
    import argparse

    parser = argparse.ArgumentParser(description='ADAM client command line utility')

    args = parser.parse_args()


if __name__ == "__main__":
    sys.exit(main() or 0)
