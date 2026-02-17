
import re
import sys
import argparse
def FatalError(msg=None):
    print("FATAL ERROR ENCOUNTERED")
    if msg: print(msg)
    print("No output generated")
    exit(1)


def sanitize(line):
    # Matches a delimiter (%) that is NOT preceded by a backslash (%)
    parts = re.split(r'(?<!\\)%', line.strip(), maxsplit=1)
    return parts[0].strip()


def parseArgs():
    if len(sys.argv) == 1:
        FatalError(f"Must provide a path to a valid file")
    parser = argparse.ArgumentParser(description="MeML Compiler")
    
    # Required positional argument
    parser.add_argument("filepath", help="Path to the .mtg file")
    
    # Optional modes (allows: --agenda --notes etc.)
    parser.add_argument("-a", "--agenda",  dest="modes", action="append_const", const="agenda")
    parser.add_argument("-c", "--chair",   dest="modes", action="append_const", const="chair")
    parser.add_argument("-n", "--notes",   dest="modes", action="append_const", const="notes")
    parser.add_argument("-m", "--minutes", dest="modes", action="append_const", const="notes")
    parser.add_argument("--all",           dest="all_modes", action="store_true")
    parser.add_argument("-o","--output",dest="output",default=None)
    args = parser.parse_args()
    # Logic to consolidate modes
    valid_modes = {"agenda", "chair", "notes"}
    if args.all_modes:
        return args.filepath, list(valid_modes),args.output
    
    # Default to 'notes' if no mode provided, or return unique set
    selected = list(set(args.modes)) if args.modes else ["notes"]
    return args.filepath, selected,args.output

