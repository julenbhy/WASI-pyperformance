import sys

def print_arguments(arg1, arg2):
    print("Argument 1:", arg1)
    print("Argument 2:", arg2)

if __name__ == "__main__":
    # Check if two arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python script.py <argument1> <argument2>")
    else:
        arg1 = sys.argv[1]
        arg2 = sys.argv[2]
        print_arguments(arg1, arg2)
