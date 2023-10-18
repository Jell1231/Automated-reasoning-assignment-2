import os

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

    def is_safe(self, v, c):
        for neighbor in self.graph[v]:
            if self.colors[neighbor] == c:
                return False
        return True

    def count_mem_k_colorings(self, k, memo, vertex):
        if vertex == self.V:
            return 1
        if (vertex, k) in memo:
            return memo[(vertex, k)]
        count = 0
        for color in range(k):
            if self.is_safe(vertex, color):
                self.colors[vertex] = color
                count += self.count_mem_k_colorings(k, memo, vertex + 1)
                self.colors[vertex] = -1
        memo[(vertex, k)] = count
        return count

    def total_memory_k_colorings(self, k):
        self.colors = [-1] * self.V
        memo = {}
        return self.count_mem_k_colorings(k, memo, 0)

    def count_naive_k_colorings(self, k, vertex=0):
        if vertex == self.V:
            return 1
        count = 0
        for color in range(k):
            if self.is_safe(vertex, color):
                self.colors[vertex] = color
                count += self.count_naive_k_colorings(k, vertex + 1)
                self.colors[vertex] = -1
        return count

    def total_naive_k_colorings(self, k):
        self.colors = [-1] * self.V
        return self.count_naive_k_colorings(k)


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


if __name__ == '__main__':
    # Specify the directory containing DIMACS graph files
    dir_str = "./data/small-dimacs/"

    # Specify the DIMACS graph file you want to analyze
    gcd_file = f"{dir_str}gcd.col"

    # Get a list of files in the directory
    directory = os.fsencode(dir_str)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)

        # Parse the DIMACS file and create the graph
        graph = parse_dimacs(f"{dir_str}{filename}")

        # Find the minimum number of registers required using greedy coloring
        min_registers = graph.greedy_coloring()
        print(f"Minimum number of registers required for {filename}: {min_registers}")

        # Use the minimum number of registers as the upper bound for k

        colors_k = min_registers
        total_colorings = graph.total_naive_k_colorings(colors_k)
        total_mem_colorings = graph.total_memory_k_colorings(colors_k)

        print(f"Total number of different {colors_k}-colorings: {total_colorings}")
