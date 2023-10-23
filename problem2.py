import os
import sys
import time

from dd.cudd import BDD

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
                print("Size;", len(vertex_ordering))
            continue
        # add the variables when the line with the number of vertices is found
        elif line.startswith('p'):
            vertices = int(line.split()[2])
            for vertex in range(1, vertices + 1):
                bdd_dimacs.add_var(f'x{vertex}')
        # add the expressions
        else:
            # remove the zero at the end
            variables = line.strip().split()[:-1]
            # create the expression
            disjunction = []
            for v in variables:
                # negations
                if v.startswith('-'):
                    disjunction.append(f'~x{v[1:]}')
                # positive
                else:
                    disjunction.append(f'x{v}')
            # add the expression to the bdd
            expression = f'({" | ".join(disjunction)})'
            u &= bdd_dimacs.add_expr(expression)
    # do model counting and return the vertex ordering
    return bdd_dimacs, u, vertex_ordering


def auto_include(bdd, expressions, order, auto_func, dimacs_name):
    f = open(f"./final_configurations2/{dimacs_name}-{auto_func}.txt", "w")
    added = 0
    negated_added = 0
    test_bdd = BDD()
    [test_bdd.add_var(var) for var in bdd.vars]
    # always include
    if auto_func == "a":
        for node in tqdm(order):
            feat = f'x{node}'
            negated_feat = f'~x{node}'
            if feat in bdd.support(expressions):
                negated_count, normal_count = get_model_counts(test_bdd, expressions, feat, bdd, negated_feat)
                if normal_count > 0:
                    f.write(f"Including {feat}\n")
                    added += 1
                    expressions &= bdd.add_expr(feat)
                elif negated_count > 0:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    expressions &= bdd.add_expr(negated_feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # always exclude
    elif auto_func == "b":
        for node in order:
            feat = f'x{node}'
            negated_feat = f'~x{node}'
            if feat in bdd.support(expressions):
                negated_count, normal_count = get_model_counts(test_bdd, expressions, feat, bdd, negated_feat)
                if negated_count > 0:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    expressions &= bdd.add_expr(negated_feat)
                elif normal_count > 0:
                    f.write(f"Including {feat}\n")
                    added += 1
                    expressions &= bdd.add_expr(feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # always include if leads to more valid configurations
    elif auto_func == "c":
        for node in tqdm(order):
            feat = f'x{node}'
            negated_feat = f'~x{node}'
            if feat in bdd.support(expressions):
                negated_count, normal_count = get_model_counts(test_bdd, expressions, feat, bdd, negated_feat)
                if normal_count > negated_count:
                    f.write(f"Including {feat}\n")
                    added += 1
                    expressions &= bdd.add_expr(feat)
                elif negated_count > 0:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    expressions &= bdd.add_expr(negated_feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # always exclude if leads to more valid configurations
    elif auto_func == "d":
        for node in tqdm(order):
            feat = f'x{node}'
            negated_feat = f'~x{node}'
            if feat in bdd.support(expressions):
                negated_count, normal_count = get_model_counts(test_bdd, expressions, feat, bdd, negated_feat)
                if negated_count > normal_count:
                    f.write(f"Excluding {feat}\n")
                    negated_added += 1
                    expressions &= bdd.add_expr(negated_feat)
                elif normal_count > 0:
                    f.write(f"Including {feat}\n")
                    added += 1
                    expressions &= bdd.add_expr(feat)
                else:
                    f.write(f"Count {feat} is {normal_count}, {negated_count}")
                    print(f"Count {feat} is {normal_count}, {negated_count}")
    # interactive mode
    else:
        added, expressions, negated_added = interactive_mode(added, test_bdd, expressions, f, bdd, negated_added, order)
    return bdd, expressions, [added, negated_added], f


def interactive_mode(added, test_bdd, expressions, f, bdd, negated_added, order):
    for node in order:
        feat = f'x{node}'
        negated_feat = f'~x{node}'
        if feat in bdd.support(expressions):
            negated_count, normal_count = get_model_counts(test_bdd, expressions, feat, bdd, negated_feat)
            incl = input(f"Include {feat}? (y/n)\n" +
                         f"Valid configurations if positive: {normal_count}; if negative: {negated_count}; (y/n)")
            if "y" in incl.lower():
                f.write(f"Including {feat}\n")
                added += 1
                expressions &= bdd.add_expr(feat)
            else:
                f.write(f"Excluding {feat}\n")
                negated_added += 1
                expressions &= bdd.add_expr(negated_feat)
    return added, expressions, negated_added


def get_model_counts(test_bdd, expressions, feat, bdd, negated_feat):
    v = bdd.copy(expressions, test_bdd)
    v &= test_bdd.add_expr(feat)
    normal_count = test_bdd.count(v)

    v = bdd.copy(expressions, test_bdd)
    v &= test_bdd.add_expr(negated_feat)
    negated_count = test_bdd.count(v)
    return negated_count, normal_count


def print_choice(choice, fname, bdd, expressions, ordering):
    start_time = time.time()
    bdd, expressions, add_arr, out_file = auto_include(bdd, expressions, ordering, choice, fname)
    # state the overall execution time, the final configuration, and the number of configuration steps made
    exec_time = time.time() - start_time
    print(f"Execution time of {fname}-{choice}: {exec_time} seconds")
    print(f"Model count: {bdd.count(expressions)}")
    print(f"Choices: {add_arr[0] + add_arr[1]}/{len(ordering)}, "
          f"of which positive: {add_arr[0]}, negative: {add_arr[1]}")
    out_file.write(f"Execution time of {fname}-{choice}: {exec_time} seconds\n")
    out_file.write(f"Model count: {bdd.count(expressions)}\n")
    out_file.write(f"Choices: {add_arr[0] + add_arr[1]}/{len(ordering)}, "
                   f"of which positive: {add_arr[0]}, negative: {add_arr[1]}\n")
    out_file.close()


if __name__ == '__main__':
    # Specify the directory containing DIMACS graph files
    dir_str = os.path.join("data", "feature-dimacs")

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
    for f in os.listdir(directory):
        # Initialize the BDD manager
        bdd = BDD()
        filename = os.fsdecode(f)
        file = os.path.join(os.fsdecode(directory), filename)

        # Parse the DIMACS file and create the graph
        print(f"Bdd {file}, {filename}: In progress...")
        bdd, expressions, vo = parse_dimacs(f"{file}", bdd)
        print(f"bdd model count {filename}: {bdd.count(expressions)}")
        # easy to run everything; change auto_choice to choice as well :)
        if auto_choice == "all":
            for choice in auto_choices:
                print_choice(choice, filename, bdd, expressions, vo)
        else:
            print_choice(auto_choice, filename, bdd, expressions, vo)

        # Find the minimum number of registers required using greedy coloring
        print(f"Bdd {filename}: Done")
