import os
from dd.cudd import BDD
from time import time

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

# Creates the bdd
def create_bdd(graph):
    # Initialize bdd and result to check later
    bdd = BDD()
    result = bdd.true

    bin_vertex_nr = (graph.V - 1).bit_length()

    # Add all possible variables 
    for i in range(bin_vertex_nr):
        bdd.add_var(f'x_{i}')
        bdd.add_var(f'x_{i}_prime')

    # Loop over all vertices in the adjacency list
    for i in range(len(graph.graph)):
        from_vertex = bin(i)[2:]
        from_vertex = f'{from_vertex.zfill(bin_vertex_nr)}'
        for j in range(len(graph.graph[i])):
            to_vertex = bin(graph.graph[i][j])[2:]
            to_vertex = f'{to_vertex.zfill(bin_vertex_nr)}'
            
            clause = []
            number = 0
            for nr in from_vertex:
                clause.append(f'!x_{number}' if nr=="0" else f'x_{number}')
                number+=1
            
            number = 0
            for nr in to_vertex:
                clause.append(f'!x_{number}_prime' if nr=="0" else f'x_{number}_prime')
                number+=1
            
            big_clause = "(" + ' & '.join(clause) + ")"
            result |= bdd.add_expr(big_clause)
            


if __name__ == '__main__':
     # Specify the directory containing DIMACS graph files
    dir_str = "./data/less-dimacs/"

    # Get a list of files in the directory
    directory = os.fsencode(dir_str)

    for file in os.listdir(directory):
        start = time()

        # Initialize the BDD manager
        filename = os.fsdecode(file)

        if (filename=="gcd.col"):        
            # Parse the DIMACS file and create the graph
            graph = parse_dimacs(f"{dir_str}{filename}")

            create_bdd(graph)