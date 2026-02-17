
import re
import sys
import argparse
def FatalError(msg=None):
    if msg: print(msg)
    print("FATAL MEML ERROR ENCOUNTERED")
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
    parser.add_argument("filepath", help="Path to the input MeML file")
    
    # Optional modes (allows: --agenda --notes etc.)
    parser.add_argument("-a", "--agenda",  dest="modes", action="append_const", const="agenda",help="Activates agenda mode")
    parser.add_argument("-c", "--chair",   dest="modes", action="append_const", const="chair",help="Activates chair mode")
    parser.add_argument("-n", "--notes", "-m","--minutes",   dest="modes", action="append_const", const="notes",help="Activates minutes mode")
    parser.add_argument("--all",           dest="all_modes", action="store_true",help="Activates agenda, chair and minutes mode")
    parser.add_argument("-o",dest="output",default=None,help="The output filename or directory",metavar="[destination]")
    args = parser.parse_args()
    # Logic to consolidate modes
    valid_modes = {"agenda", "chair", "notes"}
    if args.all_modes:
        return args.filepath, list(valid_modes),args.output
    
    # Default to 'notes' if no mode provided, or return unique set
    selected = list(set(args.modes)) if args.modes else ["notes"]
    return args.filepath, selected,args.output

