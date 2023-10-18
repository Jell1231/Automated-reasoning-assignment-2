import os
import sys
from dd import autoref as _bdd


# Function to parse the DIMACS graph file
def parse_dimacs(f, bdd_dimacs):
    with open(f, 'r') as file:
        lines = file.readlines()

    vertex_ordering = []
    u = bdd.true
    # read the lines of the dimacs file
    for line in lines[:50]:
        # ignore comments unless its a vertex ordering
        if line.startswith('c'):
            if line.split()[2] == 'vo':
                vertex_ordering = line.strip().split()[2:]
            continue
        # add the variables when the line with the number of vertices is found
        elif line.startswith('p'):
            vertices = int(line.split()[2])
            for vertex in range(1, vertices + 1):
                bdd_dimacs.add_var(f'x_{vertex}')
        # add the expressions
        else:
            # remove the zero at the end
            variables = line.strip().split()[:-1]
            # create the expression
            expression_string = ''
            for v in variables:
                # negations
                if v.startswith('-'):
                    expression_string += fr'~x_{v[1:]} | '
                else:
                    expression_string += fr'x_{v} | '
            # add the expression to the bdd
            expression = fr'({expression_string[:-3]})'
            u &= bdd_dimacs.add_expr(expression)
    # do model counting and return the vertex ordering
    return bdd_dimacs.count(u), vertex_ordering


if __name__ == '__main__':
    # Specify the directory containing DIMACS graph files
    dir_str = "./data/feature-dimacs/"

    # Specify the DIMACS graph file you want to analyze
    gcd_file = f"buildroot.dimacs"

    # Get a list of files in the directory
    directory = os.fsencode(dir_str)

    sys.setrecursionlimit(2500)
    for file in os.listdir(directory):
        # Initialize the BDD manager
        bdd = _bdd.BDD()
        filename = os.fsdecode(file)

        # Parse the DIMACS file and create the graph
        model_count, vo = parse_dimacs(f"{dir_str}{filename}", bdd)

        # Find the minimum number of registers required using greedy coloring
        print(f"Bdd {filename}: {model_count}")
