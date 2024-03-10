from pulp import *
import json

def solve_assembly_line_assignment(lines, containers):
    M = len(containers)
    N = len(lines)
    all_items = set()
    for container in containers:
        all_items = all_items.union(container["items"])
    all_items = list(all_items)
    K = len(all_items)

    print(f"Containers: {len(containers)}")
    print(f"Lines: {len(lines)}")
    print(f"Total size: {sum([line["size"] for line in lines])}")
    print(f"Items: {len(all_items)}")
    print()

    # Create a binary variable x[i][j] representing whether product i is assigned to assembly line j
    x = LpVariable.dicts("Product", [(i, j) for i in range(1, M + 1) for j in range(1, N + 1)], 0, 1, LpBinary)

    # Create a binary variable y[i][k] representing whether item k is used on assembly line j
    y = LpVariable.dicts("Item", [(j, k) for j in range(1, N + 1) for k in range(1, K + 1)], 0, 1, LpBinary)

    # Create the LP problem
    prob = LpProblem("Assembly_Line_Assignment", LpMaximize)

    # Objective function: maximize the total assignment value
    # This function is not necessary, as total sum of all products on all lines = total sum of all products in this case.
    prob += lpSum(x[i, j] for i in range(1, M + 1) for j in range(1, N + 1)), "Total_Assignment_Value"

    # Constraints: each product is assigned to exactly one assembly line
    for i in range(1, M + 1):
        prob += lpSum(x[i, j] for j in range(1, N + 1)) == 1, f"Product_Assignment_{i}"

    # Constraints: assembly line size
    for j in range(1, N + 1):
        prob += lpSum(y[j, k] for k in range(1, K + 1)) <= lines[j - 1]["size"], f"Assembly_Line_Size_{j}"

    # Constraints: link y and x variables
    for i in range(1, M + 1):
        for j in range(1, N + 1):
            for k in range(1, K + 1):
                # This constraint ensures that when x[i, j] assumes value 1 then it's item also does so.
                # This helps in checking previous constraint of size without double counting.
                if all_items[k-1] in containers[i-1]["items"]:
                    prob += y[j, k] >= x[i, j], f"Link_{i}_{k}_{j}"

    prob.writeLP("assembly_line_model.lp")

    # Solve the problem
    prob.solve(PULP_CBC_CMD(msg=1, timeLimit=60*5))

    assignment = {}
    for i in range(1, M + 1):
        for j in range(1, N + 1):
            line = lines[j-1]
            line_key = line["line_key"]
            assignment[line_key] = {"available_size": line["size"], "containers": [], "items": []}

    for i in range(1, M + 1):
        contianer = containers[i-1]
        for j in range(1, N + 1):
            line = lines[j-1]
            line_key = line["line_key"]
            if value(x[i, j]) == 1:
                assignment[line_key]["containers"].append(contianer["sku_code"])
    
    for j in range(1, N + 1):
        line = lines[j-1]
        line_key = line["line_key"]
        for k in range(1, K + 1):
            if value(y[j, k]) == 1:
                assignment[line_key]["available_size"] -= 1
                assignment[line_key]["items"].append(all_items[k-1])
    
    # Print the results
    print(f"Status: {LpStatus[prob.status]}")
    print(f"Optimal Assignment")
    for line_key in assignment:
        print(f"Line - {line_key}[{assignment[line_key]["available_size"]}] Containers: {assignment[line_key]["containers"]} Items: {assignment[line_key]["items"]}")    
                

with open('./data.json') as f:
    data = json.load(f)
    lines = []
    for line in data["lines"]:
        lines.append({"line_key": line["lineKey"], "size": line["size"]})
    containers = []
    for container in data["containers"]:
        container_items = container["items"]
        items = []
        for item in container_items:
            items.append(f"{item["skuCode"]}-{item["part"]}")
        containers.append({"sku_code": container["skuCode"], "items": set(items)})

    # lines = [{"line_key": "1", "size": 3}, {"line_key": "2", "size": 4}, {"line_key": "3", "size": 4}]
    # containers = [
    #     {"sku_code": "C1", "items": {1, 2, 3}}, 
    #     {"sku_code": "C2", "items": {2, 3, 4}}, 
    #     {"sku_code": "C3", "items": {1, 3, 5}}, 
    #     {"sku_code": "C4", "items": {4, 5}}, 
    #     {"sku_code": "C5", "items": {1, 2, 4, 5}},
    # ]  # Products as sets of items
    solve_assembly_line_assignment(lines, containers)
