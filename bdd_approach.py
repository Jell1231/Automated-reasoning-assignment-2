import os
from dd.autoref import BDD


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


def create_bdd_max_opperman(bdd, adjacency_list, colors):
    vertices = len(adjacency_list)
    for c in range(colors):
        for n in range(vertices):
            bdd.add_var(f'x_{n}_{c}')
    expression_string = ''
    for n in range(len(adjacency_list)):
        for neighbor in adjacency_list[n]:
            for c in range(colors):
                expression_string += fr'(~x_{n}_{c} \/ ~x_{neighbor}_{c}) /\ '
    print(expression_string[:-4])
    u = bdd.add_expr(expression_string[:-4])
    return u


def create_bdd(f, color_nr):
    bdd = BDD()

    with open(f, 'r') as file:
        lines = file.readlines()

    # Create list of variables and clauses
    vars = []
    clauses = []

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
            for i in range(color_nr):
                vars.append(f'x_{u}_{i}')
                vars.append(f'x_{v}_{i}')
                clauses.append(f'(!x_{u}_{i} | !x_{v}_{i})')
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
        clauses.append(" | ".join(clause))
    
    # Create all BDD variables
    [bdd.add_var(var) for var in vars]

    cnf = bdd.true
    for i in range(len(clauses)):
        cnf &= bdd.add_expr(clauses[i])

    print(f'k: {color_nr}, size: {len(cnf)}, models: {bdd.count(cnf)}')
    print()
    
    # bdd.dump(f'bdds/{filename[:-4]}.pdf', roots=[bdd])
            


if __name__ == '__main__':
    # Specify the directory containing DIMACS graph files
    dir_str = "./data/small-dimacs/"

    # Specify the DIMACS graph file you want to analyze
    gcd_file = f"gcd.col"

    # Get a list of files in the directory
    directory = os.fsencode(dir_str)

    for file in os.listdir(directory):
        # Initialize the BDD manager
        filename = os.fsdecode(file)

        # Parse the DIMACS file and create the graph
        graph = parse_dimacs(f"{dir_str}{filename}")

        # Find the minimum number of registers required using greedy coloring
        min_registers = graph.greedy_coloring()
        print(f"Minimum number of registers required for {filename}: {min_registers}")

        # Use the minimum number of registers as the upper bound for k
        # if (filename=="gcd.col"):
        create_bdd(f"{dir_str}{filename}", min_registers)
        # res_bdd = create_bdd(bdd, graph.graph, min_registers)
        # bdd.dump(f'bdds/{filename[:-4]}.pdf', roots=[res_bdd])
