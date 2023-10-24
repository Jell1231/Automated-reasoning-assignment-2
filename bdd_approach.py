import os
from time import time
from dd.cudd import BDD


# Define a Graph class to represent the graph and perform coloring
class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = [[] for _ in range(vertices)]

    def add_edge(self, u, v):
        # Add an edge between vertices u and v in the graph
        self.graph[u].append(v)
        self.graph[v].append(u)

    def greedy_coloring(self):
        # Greedy graph coloring algorithm
        result_colors = [-1] * self.V  # Initialize color assignments
        result_colors[0] = 0  # Assign the first vertex the first color
        already_colored = [False] * self.V  # Track available colors

        for u in range(1, self.V):
            for neighbor in self.graph[u]:
                # check if neighbor is not colored
                if result_colors[neighbor] != -1:
                    # the neighbor should still be colored
                    already_colored[result_colors[neighbor]] = True

            node_color = 0
            # find a node that is not colored yet
            while node_color < self.V:
                if not already_colored[node_color]:
                    # we found one that is not yet colored, so this is the number of the next color
                    break
                node_color += 1

            result_colors[u] = node_color  # Assign the minimum available color
            for neighbor in self.graph[u]:
                # say that the neighbors without colors should still be colored
                if result_colors[neighbor] != -1:
                    already_colored[result_colors[neighbor]] = False

        return max(result_colors) + 1  # Return the total number of colors used


# Function to parse the DIMACS graph file
def parse_dimacs(f):
    with open(f, 'r') as file:
        lines = file.readlines()

    vertices = None
    edges = []

    for line in lines:
        if line.startswith('c'):
            # Ignore comments
            continue
        elif line.startswith('p'):
            vertices = int(line.split()[2])
        elif line.startswith('e'):
            _, u, v = line.strip().split()
            edges.append((int(u) - 1, int(v) - 1))

    if vertices is None:
        raise ValueError("No 'p' line found in the DIMACS file.")

    g = Graph(vertices)
    for u, v in edges:
        g.add_edge(u, v)  # Add edges to the graph
    return g


def create_bdd(f, color_nr):
    bdd = BDD()
    result = bdd.true

    with open(f, 'r') as file:
        lines = file.readlines()

    vars = []

    # Loop over the input file lines
    for line in lines:
        if line.startswith('c'):
            # Ignore comments
            continue
        elif line.startswith('p'):
            # Ignore describing line
            continue
        elif line.startswith('e'):
            _, u, v = line.strip().split()
            # Add to variables list, add clause that two vertices may not be the same color
            clause = []
            for i in range(color_nr):
                vars.append(f'x_{u}_{i}')
                vars.append(f'x_{v}_{i}')
                bdd.add_var(f'x_{u}_{i}')
                bdd.add_var(f'x_{v}_{i}')

                c = f'(!x_{u}_{i} | !x_{v}_{i})'
                result &= bdd.add_expr(c)
        else:
            raise Exception("This should not happen")
    
    # Sort such that we can use the list later
    vars = sorted(set(vars))
    
    # Create clauses for the statement, a vertex may have only one color.
    for i in range(0, len(vars), color_nr):
        variable_group = vars[i:i+color_nr]
        clause = []

        # Create a clause for each combination of variables in the group
        for j in range(color_nr):
            variable_combo = [f"{'!' if l != j else ''}{variable}" for l, variable in enumerate(variable_group)]
            clause.append("(" + " & ".join(variable_combo) + ")")

        # Combine the individual clauses with ' | ' to ensure only one is true
        u = bdd.false
        for c in clause:
            u |= bdd.add_expr(c)
        result &= u

        # c = " | ".join(clause)
        # result &= bdd.add_expr(c)
    
    # print(bdd.statistics())
    print(f'k: {color_nr}, size: {len(result)}, models: {bdd.count(result)}')


################################################
# non-working :)))))
################################################          
def create_bit_encoded_bdd(f, color_nr):
    bdd = BDD()

    with open(f, 'r') as file:
        lines = file.readlines()

    # Create list of variables and clauses
    vars = []
    clauses = []
    nodes = []
    bits_needed = (color_nr-1).bit_length()

    # Loop over the input file lines
    for line in lines:
        if line.startswith('c'):
            # Ignore comments
            continue
        elif line.startswith('p'):
            # Ignore describing line
            continue
        elif line.startswith('e'):
            _, u, v = line.strip().split()
            nodes.append(u)
            nodes.append(v)
            # Add to variables list, add clause that two vertices may not be the same color
            # This time we use a bit representation for this. So we make log(color_nr) variables for each vertex, which is the
            # nr of bits needed to represent the amount of colors.
            for i in range(bits_needed):
                vars.append(f'x_{u}_{i}')
                vars.append(f'x_{v}_{i}')
            
            for i in range(color_nr):
                current = bin(i)[2:]
                current = f'{current.zfill(bits_needed)}'

                for j in range(bits_needed):
                    clauseU = []
                    clauseV = []
                    for nr in current:
                        clauseU.append(f'!x_{u}_{j}' if nr=="0" else f'x_{u}_{j}')
                        clauseV.append(f'!x_{v}_{j}' if nr=="0" else f'x_{v}_{j}')
                clauses.append("!(" + " & ".join(clauseU) + ") | !(" + " & ".join(clauseV) + ")")
        else:
            raise Exception("This should not happen")
    
    # Make vars a set such that no duplicates are present
    vars = set(vars)
    nodes = set(nodes)
    
    # Create clauses for the statement, a vertex may have only one color.
    temp_vars = []
    for node in nodes:
        for i in range(color_nr):
            current = bin(i)[2:]
            current = f'{current.zfill(bits_needed)}'

            for j in range(bits_needed):
                clause = []
                for nr in current:
                    clause.append(f'!x_{node}_{j}' if nr=="0" else f'x_{node}_{j}')
            temp_vars.append("(" + " & ".join(clause) + ")")

    for i in range(0, len(nodes)*color_nr, color_nr):
        variable_group = temp_vars[i:i+color_nr]
        clause = []

        # Create a clause for each combination of variables in the group
        for j in range(color_nr):
            variable_combo = [f"{'!' if l != j else ''}{variable}" for l, variable in enumerate(variable_group)]
            clause.append("(" + " & ".join(variable_combo) + ")")

        # Combine the individual clauses with ' | ' to ensure only one is true    
        clauses.append(" | ".join(clause))
    
    # Create all BDD variables
    [bdd.add_var(var) for var in vars]

    cnf = bdd.true
    for clause in clauses:
        cnf &= bdd.add_expr(clause)

    print(f'k: {color_nr}, size: {len(cnf)}, models: {bdd.count(cnf)}')
    print()
##########################################################################

if __name__ == '__main__':
    # Specify the directory containing DIMACS graph files
    dir_str = "./data/small-dimacs/"

    # Specify the DIMACS graph file you want to analyze
    gcd_file = f"gcd.col"

    # Get a list of files in the directory
    directory = os.fsencode(dir_str)

    for file in os.listdir(directory):
        start = time()
        # Initialize the BDD manager
        filename = os.fsdecode(file)

        # Parse the DIMACS file and create the graph
        graph = parse_dimacs(f"{dir_str}{filename}")

        # Find the minimum number of registers required using greedy coloring
        min_registers = graph.greedy_coloring()
        print(f"Minimum number of registers required for {filename}: {min_registers}")

        # Use the minimum number of registers as the upper bound for k
        # if (filename=="zeroin-less.col"):
        #     create_bdd(f"{dir_str}{filename}", min_registers)
        create_bdd(f"{dir_str}{filename}", min_registers)
        stop = time()
        print(f"Runtime of {file}: ", stop-start)
        print()