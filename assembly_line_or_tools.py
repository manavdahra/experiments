from ortools.linear_solver import pywraplp
import json

def solve_assembly_line_assignment(lines, containers):
    M = len(containers)
    N = len(lines)
    all_items = set()
    for container in containers:
        all_items = all_items.union(container["items"])
    all_items = list(all_items)
    K = len(all_items)

    solver = pywraplp.Solver.CreateSolver("BOP_INTEGER_PROGRAMMING")
    if not solver:
        return

    # Create a binary variable x[i][j] representing whether product i is assigned to assembly line j
    x = {}
    for i in range(1, M+1):
        for j in range(1, N+1):
            x[(i, j)] = solver.BoolVar(f"Product_{i}_{j}")

    # Create a binary variable y[i][k] representing whether item k is used on assembly line j
    y = {}
    for j in range(1, N+1):
        for k in range(1, K+1):
            y[(j, k)] = solver.BoolVar(f"Item_{j}_{k}")

    # Create the LP problem
    objective = solver.Objective()
    for i in range(1, M+1):
        for j in range(1, N+1):
            objective.SetCoefficient(x[(i, j)], 1)
    
    objective.SetMaximization()

    # Constraints: a product is assigned to only one
    for i in range(1, M + 1):
        solver.Add(solver.Sum(x[(i, j)] for j in range(1, N + 1)) == 1)

    # Constraints: assembly line size
    for j in range(1, N + 1):
        solver.Add(solver.Sum(y[(j, k)] for k in range(1, K + 1)) <= lines[j - 1]["size"])

    # Constraints: link y and x variables
    for i in range(1, M + 1):
        for j in range(1, N + 1):
            for k in range(1, K + 1):
                # This constraint ensures that when x[i, j] assumes value 1 then it's item also does so.
                # This helps in checking previous constraint of size without double counting.
                if all_items[k-1] in containers[i-1]["items"]:
                    solver.Add(y[(j, k)] >= x[(i, j)])

    # Solve the problem
    print(f"Solving with {solver.SolverVersion()}")
    solver.EnableOutput()
    solver.SetTimeLimit(1000*60*5)
    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL and status != pywraplp.Solver.FEASIBLE:
        print("The problem doesnt have a feasible solution")
        return
    
    assignment = {}
    for i in range(1, M + 1):
        for j in range(1, N + 1):
            line = lines[j-1]
            line_key = line["line_key"]
            assignment[line_key] = {"available_size": line["size"], "size": line["size"], "containers": [], "items": []}

    for i in range(1, M + 1):
        contianer = containers[i-1]
        for j in range(1, N + 1):
            line = lines[j-1]
            line_key = line["line_key"]
            if x[(i, j)].solution_value() > 0:
                assignment[line_key]["containers"].append(contianer["sku_code"])
    
    for j in range(1, N + 1):
        line = lines[j-1]
        line_key = line["line_key"]
        for k in range(1, K + 1):
            if y[(j, k)].solution_value() > 0:
                assignment[line_key]["available_size"] -= 1
                assignment[line_key]["items"].append(all_items[k-1])
    
    # Print the results
    print("\n################## Result ###################\n")
    print(f"Optimal Assignment")
    print(f"Containers: {len(containers)}")
    print(f"Lines: {len(lines)}")
    print(f"Items: {len(all_items)}")
    print(f"Total size: {sum([line["size"] for line in lines])}")
    for line_key in assignment:
        print(f"Line - {line_key}[{assignment[line_key]["available_size"]}/{assignment[line_key]["size"]}] Containers: {assignment[line_key]["containers"]} Items: {assignment[line_key]["items"]}")
                

with open('./data.json') as f:
    # data = json.load(f)
    # lines = []
    # for line in data["lines"]:
    #     lines.append({"line_key": line["lineKey"], "size": line["size"]})
    # containers = []
    # for container in data["containers"]:
    #     container_items = container["items"]
    #     items = []
    #     for item in container_items:
    #         items.append(f"{item["skuCode"]}-{item["part"]}")
    #     containers.append({"sku_code": container["skuCode"], "items": set(items)})

    lines = [{"line_key": "1", "size": 3}, {"line_key": "2", "size": 4}, {"line_key": "3", "size": 4}]
    containers = [
        {"sku_code": "C1", "items": {1, 2, 3}}, 
        {"sku_code": "C2", "items": {2, 3, 4}}, 
        {"sku_code": "C3", "items": {1, 3, 5}}, 
        {"sku_code": "C4", "items": {4, 5}}, 
        {"sku_code": "C5", "items": {1, 2, 4, 5}},
    ]  # Products as sets of items
    solve_assembly_line_assignment(lines, containers)
