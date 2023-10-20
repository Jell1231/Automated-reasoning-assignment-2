import os
import sys
import time

from dd import autoref as _bdd

# Function to parse the DIMACS graph file
from tqdm import tqdm


def parse_dimacs(f, bdd_dimacs):
    with open(f, 'r') as file:
        lines = file.readlines()

    vertex_ordering = []
    u = bdd_dimacs.true
    # read the lines of the dimacs file
    for line in lines:
        # ignore comments unless its a vertex ordering
        if line.startswith('c'):
            if line.split()[1] == 'vo':
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
    return bdd_dimacs, u, vertex_ordering


def auto_include(features, exprs, order, auto_func):
    f = open(f"./final_configurations2/{auto_func}.txt", "w")
    added = 0
    negated_added = 0
    b = _bdd.BDD()
    [b.add_var(var) for var in features.vars]
    # always include
    if auto_func == "a":
        for node in tqdm(order):
            feat = fr'x_{node}'
            negated_feat = fr'~x_{node}'
            if feat in features.support(exprs):
                negated_count, normal_count = get_model_counts(b, exprs, feat, features, negated_feat)
                if normal_count > 0:
                    f.write(f"Including {feat}\n")
                    added += 1
                    exprs &= features.add_expr(feat)
                elif negated_count > 0:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    exprs &= features.add_expr(negated_feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # always exclude
    elif auto_func == "b":
        for node in tqdm(order):
            feat = fr'x_{node}'
            negated_feat = fr'~x_{node}'
            if feat in features.support(exprs):
                negated_count, normal_count = get_model_counts(b, exprs, feat, features, negated_feat)
                if negated_count > 0:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    exprs &= features.add_expr(negated_feat)
                elif normal_count > 0:
                    f.write(f"Including {feat}\n")
                    added += 1
                    exprs &= features.add_expr(feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # always include if leads to more valid configurations
    elif auto_func == "c":
        for node in tqdm(order):
            feat = fr'x_{node}'
            negated_feat = fr'~x_{node}'
            if feat in features.support(exprs):
                negated_count, normal_count = get_model_counts(b, exprs, feat, features, negated_feat)
                if normal_count > negated_count:
                    f.write(f"Including {feat}\n")
                    added += 1
                    exprs &= features.add_expr(feat)
                elif negated_count > 0:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    exprs &= features.add_expr(negated_feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # always exclude if leads to more valid configurations
    elif auto_func == "d":
        for node in tqdm(order):
            feat = fr'x_{node}'
            negated_feat = fr'~x_{node}'
            if feat in features.support(exprs):
                negated_count, normal_count = get_model_counts(b, exprs, feat, features, negated_feat)
                if negated_count > normal_count:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    exprs &= features.add_expr(negated_feat)
                elif normal_count > 0:
                    f.write(f"Including {feat}\n")
                    added += 1
                    exprs &= features.add_expr(feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # interactive mode
    else:
        added, exprs, negated_added = interactive_mode(added, b, exprs, f, features, negated_added, order)
    f.close()
    return features, exprs, [added, negated_added]


def interactive_mode(added, b, exprs, f, features, negated_added, order):
    for node in order:
        feat = fr'x_{node}'
        negated_feat = fr'~x_{node}'
        if feat in features.support(exprs):
            negated_count, normal_count = get_model_counts(b, exprs, feat, features, negated_feat)
            incl = input(f"Include {feat}? (y/n)\n" +
                         f"Valid configurations if positive: {normal_count}; if negative: {negated_count}; (y/n)")
            if "y" in incl.lower():
                f.write(f"Including {feat}\n")
                added += 1
                exprs &= features.add_expr(feat)
            else:
                f.write(f"Excluding {feat}\n")
                negated_added += 1
                exprs &= features.add_expr(negated_feat)
    return added, exprs, negated_added


def get_model_counts(b, exprs, feat, features, negated_feat):
    v = features.copy(exprs, b)
    v &= b.add_expr(feat)
    normal_count = b.count(v)

    v = features.copy(exprs, b)
    v &= b.add_expr(negated_feat)
    negated_count = b.count(v)
    return negated_count, normal_count


def print_choice(choice, f_bdd, ex, ordering):
    start_time = time.time()
    test_bdd = _bdd.BDD()
    [test_bdd.add_var(var) for var in f_bdd.vars]
    test_expressions = f_bdd.copy(ex, test_bdd)
    bdd_final, expressions_final, add_arr = auto_include(test_bdd, test_expressions, vo, choice)
    # state the overall execution time, the final configuration, and the number of configuration steps made
    exec_time = time.time() - start_time
    print(f"Execution time of {choice}: {exec_time} seconds")
    print(f"Model count: {bdd_final.count(expressions_final)}")
    print(f"Choices: {add_arr[0] + add_arr[1]}/{len(vo)}, of which positive: {add_arr[0]}, negative: {add_arr[1]}")


if __name__ == '__main__':
    # Specify the directory containing DIMACS graph files
    dir_str = "./data/feature-dimacs/"

    # Specify the DIMACS graph file you want to analyze
    gcd_file = f"buildroot.dimacs"

    # Get a list of files in the directory
    directory = os.fsencode(dir_str)
    auto_choice = input("""(a) If there is a choice to include a feature, always include it.
(b) If there is a choice to exclude a feature, always exclude it.
(c) Always include a feature if this feature would lead to more valid configurations than possible when excluding it (under the assumption of the already configured features).
(d) Always exclude a feature if this feature would lead to more valid configurations than possible when including it (under the assumption of the already configured features).
(e) interactive mode, for each possible decision in a step the number of valid configurations after the decision will be displayed.
""")
    auto_choices = ["a", "b", "c", "d"]

    sys.setrecursionlimit(2500)
    for file in os.listdir(directory):
        # Initialize the BDD manager
        bdd = _bdd.BDD()
        filename = os.fsdecode(file)

        # Parse the DIMACS file and create the graph
        print(f"Bdd {filename}: In progress...")
        features_bdd, expressions, vo = parse_dimacs(f"{dir_str}{filename}", bdd)
        print(f"bdd model count {filename}: {features_bdd.count(expressions)}")
        # easy to run everything; change auto_choice to choice as well :)
        if auto_choice == "all":
            for choice in auto_choices:
                print_choice(choice, features_bdd, expressions, vo)
        else:
            print_choice(auto_choice, features_bdd, expressions, vo)

        # Find the minimum number of registers required using greedy coloring
        print(f"Bdd {filename}: Done")
