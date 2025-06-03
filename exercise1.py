'''
We read a txt file, outputs:
- Dict of revenues
- Dict of scenarios
- capacity
'''
def read_data():
    revenue_dict = {}
    scenarios_dict = {}
    with open('20items_50capacity_50scens.txt') as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                n_items = int(line.split(",")[1])
            elif cnt == 1:
                scenarios = int(line.split(",")[1])
            elif cnt == 2:
                capacity = int(line.split(",")[1])
            else:
                cnt += 1
                break
            cnt += 1
        for line in f:
            if 4 <= cnt < 4 + n_items:
                it_raw, rev_raw = line.split(",")
                item_idx = int(it_raw)
                revenue = int(rev_raw)
                revenue_dict[item_idx] = revenue
            elif 4 + n_items + 1 <= cnt:
                scen_raw = line.split(",")
                scenario_id = int(scen_raw[0])
                scenario_p = float(scen_raw[1])
                scenario_weights = []
                for i in range(20):
                    scenario_weights.append(int(scen_raw[2+i]))
                scenarios_dict[scenario_id] = {"p": scenario_p, "w": scenario_weights}
            cnt += 1
    return revenue_dict, scenarios_dict, capacity

def stochastic_knapsack_stochastic_model(n_items, revenue_dict, penalize_by, scenarios_dict, n_scenarios, cap):
    from pyscipopt import Model, quicksum
    model = Model()
    x = {}
    for i in range(n_items):
        x[i] = model.addVar(vtype='B', name='x_{}'.format(i))
    z = {}
    for s in range(n_scenarios):
        z[s] = model.addVar(vtype='C', lb=0, name='z_{}'.format(s))
    constr_1 = {}
    constr_2 = {}
    for s in range(n_scenarios):
        constr_1[s] = model.addCons(quicksum(scenarios_dict[s]["w"][i]*x[i] for i in range(n_items)) - z[s] <= cap, name="cons_1_{}".format(s))
        constr_2[s] = model.addCons(z[s] >= 0)
    model.setObjective(quicksum(x[i]*revenue_dict[i] for i in range(n_items)) - penalize_by*quicksum(scenarios_dict[s]["p"]*z[s] for s in range(n_scenarios)), sense="maximize")
    return model

def run_stochastic_knapsack_main_model():
    revenue_dict, scenarios_dict, capacity = read_data()
    model=stochastic_knapsack_stochastic_model(len(revenue_dict.keys()), revenue_dict, 1, scenarios_dict, len(scenarios_dict.keys()), capacity)

    model.optimize()

    solve_time = model.getSolvingTime()
    num_nodes = model.getNTotalNodes() # Note that getNNodes() is only the number of nodes for the current run (resets at restart)
    obj_val = model.getObjVal()
    print("The parameter for time is {}".format(model.getParam("limits/time")))
    print("Solved in {}s, Number of nodes {}.\nObjective value {}".format(solve_time, num_nodes, obj_val))
    model_vars = model.getVars()
    for model_var in model_vars:
        print(f"Variable {model_var.name} has value {model.getVal(model_var)}")

def stochastic_knapsack_deterministic_model(weights, n_items, n_scenarios, cap, revenue_dict):
    from pyscipopt import Model, quicksum

    model = Model()
    x = {}
    for i in range(n_items):
        x[i] = model.addVar(vtype='B', name='x_{}'.format(i))
    constr_1 = model.addCons( quicksum(weights[i] * x[i] for i in range(n_items)) <= cap, name="cons_1")

    model.setObjective(quicksum(revenue_dict[i] * x[i] for i in range(n_items)) , sense="maximize")
    return model

def run_stochastic_knapsack_deterministic_model(penalize_by):
    revenue_dict, scenarios_dict, capacity = read_data()

    n_items = len(revenue_dict.keys())
    n_scenarios = len(scenarios_dict.keys())

    weights_dict = { i:{"prob": [], "weight": []} for i in range(n_items)}

    for weight_idx in scenarios_dict:
        prob = scenarios_dict[weight_idx]["p"]
        weight = scenarios_dict[weight_idx]["w"]
        for i in range(n_items):
            weights_dict[i]["p"].append(prob)
        for i in range(n_items):
            weights_dict[i]["w"].append(weight[i])
    
    weights_raw = [[weights_dict[i]["prob"][j] * weights_dict[i]["weight"][j] for j in range(n_scenarios) ] for i in weights_dict]
    weights = [sum(weights_raw[i]) for i in range(n_items)]

    model=stochastic_knapsack_stochastic_model(weights, n_items,n_scenarios, capacity, revenue_dict)

    x = {}
    model.optimize()
    model_vars = model.getVars()
    for model_var in model_vars:
        x[int(model_var.name.split("_"[1]))] = model.getVal(model_var)
    
    total_weighted_excess = 0
    for scenario in scenarios_dict:
        prob = scenarios_dict[scenario]["p"]
        scenario_weights = scenarios_dict[scenario]["w"]
        scenario_weight = 0
        for i in range(n_items):
            scenario_weight += x[i] * scenario_weights[i]
        if scenario_weight > capacity:
            total_weighted_excess += scenario_weight*prob
    return total_weighted_excess * penalize_by