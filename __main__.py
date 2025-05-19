from swfparser import SWFParser

import sys

def main():
    if len(sys.argv) == 1:
        print(f"usage: __main__.py SWF_FILE.swf")
        return

    swf = SWFParser(sys.argv[1])
    swf.parse()

    for abc in swf.abcs.values():
        print(abc)

if __name__ == "__main__":
    main()