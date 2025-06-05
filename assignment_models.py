def read_customer_to_consolidation_data(file="data_files/consol_cust_moves.txt"):
    exit_dict = {}
    with open(file) as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                continue
            else:
                line_data = line.split(",")
                exit_dict[int(line_data[0]), line_data[1]] = {"travel_times": int(line_data[2]),"cost": int(line_data[3])}
            cnt += 1
    return exit_dict

def read_consolidation_to_customer_data(file="data_files/cust_consol_moves.txt"):
    access_dict = {}
    with open(file) as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                continue
            else:
                line_data = line.split(",")
                access_dict[int(line_data[0]), line_data[1]] = {"travel_times": int(line_data[2]),"cost": int(line_data[3])}
            cnt += 1
    return access_dict

def read_customers_data(file="data_files/customers.txt"):
    customer_dict = {}
    with open(file) as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                continue
            else:
                line_data = line.split(",")
                customer_dict[int(line_data[0])] = {"pick-up_day": int(line_data[1]),"service": int(line_data[2]), "unit_revenue": int(line_data[3]), "dedicated_cost": int(line_data[4])}
            cnt += 1
    return customer_dict

def read_legs_data(file="data_files/legs.txt"):
    legs_dict = {}
    with open(file) as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                continue
            else:
                line_data = line.split(",")
                legs_dict[line_data[0], line_data[1]] = {"travel_times": int(line_data[2])}
            cnt += 1
    return legs_dict

def read_cargo_legs_data(file="data_files/passenger_cargo_legs.txt"):
    cargo_legs_dict = {}
    with open(file) as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                continue
            else:
                line_data = line.split(",")
                cargo_legs_dict[line_data[0], line_data[1]] = {"day": int(line_data[2]), "block_cost": int(line_data[3]), "block_capacity": int(line_data[4]), "cargo_block_capacity": int(line_data[5])}
            cnt += 1
    return cargo_legs_dict

def read_scenario_data(pattern="100"):
    import glob
    scenario_instance_namefiles = glob.glob("{}*.txt".format(pattern))
    scenario_dict = {}
    for file in scenario_instance_namefiles:
        name_split = file.split("_")
        n_cust = int(name_split[0])
        n_scenarios = int(name_split[2])
        scenario_dict[n_cust, n_scenarios] = {i: {"p": -1, "d": []} for i in range(n_scenarios)}
        with open(file) as f:
            cnt = 0
            for line in f:
                if cnt == 0:
                    continue
                else:
                    line_data = line.split(",")
                    scenario_dict[n_cust, n_scenarios][cnt-1]["p"] = float(line_data[0])
                    scenario_dict[n_cust, n_scenarios][cnt-1]["d"] = [float(line_data[i]) for i in range(1, len(line_data))]
                cnt += 1
    return scenario_dict

'''
We read a txt file, outputs:
- Dict of revenues
- Dict of scenarios
- capacity
'''
def read_data():

    exit_dict = read_customer_to_consolidation_data()
    access_dict = read_consolidation_to_customer_data()
    customer_dict = read_customers_data()
    legs_dict = read_legs_data()
    cargo_legs_dict = read_cargo_legs_data()
    scenario_dict = read_scenario_data()

    return

def stoch_FFP_stochastic_model():
    from pyscipopt import Model, quicksum
    model = Model()

    x = {}
    y = {}
    z = {}

    for s in range(n_scenarios):
        for c in range(n_cust):
            for p in range(n_paths):
                for d in range(n_days):
                    x[c,p,d,s] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}_{}'.format(c,p,d,s))
    
    for l in range(n_legs):
        for d in range(n_days):
            y[l,d] = model.addVar(vtype='I', lb=0, name='y_{}_{}'.format(l,d))
    
    for s in range(n_scenarios):
        for c in range(n_cust):
            z[c,s] = model.addVar(vtype='C', lb=0, name='z_{}_{}'.format(c,s))
    
    model.setObjective((
        quicksum(scenario_chance[s] * revenue[c] * z[c,s] for c in range(n_cust) for s in range(n_scenarios))
        - quicksum(capacity_cost[l][d] * y[l,d] for l in range(n_legs) for d in range(n_days))
        - quicksum(scenario_chance[s] * path_cost[p][c] * x[c,p,d,s] for d in days_per_customer_path[c][p] for p in paths_of_customer[c] for c in range(n_cust) for s in range(n_scenarios))
        ), sense="maximize")
    
    constraint_demand = {}
    constraint_z_c = {}
    constraint_enabled_cap = {}
    for s in range(n_scenarios):
        for c in range(n_cust):
            constraint_demand[c,s] = model.addCons(z[c,s] <= demand[c][s], name="cons1_{}_{}".format(c,s))
            constraint_z_c[c,s] = model.addCons( quicksum( x[c,p,d,s] for d in days_per_customer_path[c][p] for p in paths_of_customer[c]) == z[c,s], name="cons2_{}_{}".format(c,s) )
        for l in range(n_legs):
            for d in range(n_days):
                constraint_enabled_cap[l,d,s] = model.addCons(quicksum(x[c,p,d,s] for d in day_for_leg_in_path[c][p] for p in paths_of_customer[c] for c in range(n_cust)) <= unit_size[l][d]*y[l,d], name="cons3_{}_{}".format(l,d))
    
    return model

def stoch_FFP_customer_commitment():
    from pyscipopt import Model, quicksum
    model = Model()

    x = {}
    y = {}
    z = {}
    o = {}

    for s in range(n_scenarios):
        for c in range(n_cust):
            for p in range(n_paths):
                for d in range(n_days):
                    x[c,p,d,s] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}_{}'.format(c,p,d,s))
            for e in range(n_dedicated_paths):
                for d in range(n_days):
                    o[c,e,d,s] = model.addVar(vtype='C', lb=0, name='o_{}_{}_{}_{}'.format(c,e,d,s))
    
    for l in range(n_legs):
        for d in range(n_days):
            y[l,d] = model.addVar(vtype='I', lb=0, name='y_{}_{}'.format(l,d))
    
    for c in range(n_cust):
        z[c] = model.addVar(vtype='C', lb=0, name='z_{}'.format(c))

    model.setObjective((
        quicksum(scenario_chance[s] * demand[c][s] * revenue[c] * z[c,s] for c in range(n_cust) for s in range(n_scenarios))
        - quicksum(capacity_cost[l][d] * y[l,d] for l in range(n_legs) for d in range(n_days))
        - quicksum(scenario_chance[s] * path_cost[p][c] * x[c,p,d,s] for d in days_per_customer_path[c][p] for p in paths_of_customer[c] for c in range(n_cust) for s in range(n_scenarios))
        - quicksum(scenario_chance[s] * dedicated_path_cost[e][c] * o[c,e,d,s] for d in days_per_customer_dedicated_path[c][e] for e in dedicated_paths_of_customer[c] for c in range(n_cust) for s in range(n_scenarios))
        ), sense="maximize")
    
    constraint_demand = {}
    constraint_capacity = {}
    for s in range(n_scenarios):
        for c in range(n_cust):
            constraint_demand[c] = model.addCons((
                quicksum(x[c,p,d,s] for d in days_per_customer_path[c][p] for p in paths_of_customer[c])
                + quicksum(o[c,e,d,s] for d in days_per_customer_dedicated_path[c][p] for e in dedicated_paths_of_customer[c])
                == demand[c][s], z[c]
            ), name="cons1_{}_{}".format(c,s))
        for l in range(n_legs):
            for d in range(n_days):
                constraint_capacity[l,d,s] = model.addCons((
                    quicksum(x[c,p,d,s] for d in day_for_leg_in_path[c][p] for p in paths_of_customer[c] for c in range(n_cust))
                    <= unit_size[l][d] * y[l][d]
                ), name="cons2_{}_{}_{}".format(l,d,s))

    return model
    
def stoch_FFP_dedicated_uncertainty():
    from pyscipopt import Model, quicksum
    model = Model()

    x = {}
    y = {}
    z = {}
    o = {}

    for s in range(n_scenarios):
        for c in range(n_cust):
            for p in range(n_paths):
                for d in range(n_days):
                    x[c,p,d,s] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}_{}'.format(c,p,d,s))
            for e in range(n_dedicated_paths):
                for d in range(n_days):
                    o[c,e,d,s] = model.addVar(vtype='C', lb=0, name='o_{}_{}_{}_{}'.format(c,e,d,s))
    
    for l in range(n_legs):
        for d in range(n_days):
            y[l,d] = model.addVar(vtype='I', lb=0, name='y_{}_{}'.format(l,d))
    
    for c in range(n_cust):
        z[c] = model.addVar(vtype='C', lb=0, name='z_{}'.format(c))

    model.setObjective((
        quicksum(scenario_chance[s] * demand[c][s] * revenue[c] * z[c,s] for c in range(n_cust) for s in range(n_scenarios))
        - quicksum(capacity_cost[l][d] * y[l,d] for l in range(n_legs) for d in range(n_days))
        - quicksum(scenario_chance[s] * path_cost[p][c] * x[c,p,d,s] for d in days_per_customer_path[c][p] for p in paths_of_customer[c] for c in range(n_cust) for s in range(n_scenarios))
        - quicksum(scenario_chance[s] * dedicated_path_cost_stochastic[e][c][s] * o[c,e,d,s] for d in days_per_customer_dedicated_path[c][e] for e in dedicated_paths_of_customer[c] for c in range(n_cust) for s in range(n_scenarios))
        ), sense="maximize")
    
    constraint_demand = {}
    constraint_capacity = {}
    for s in range(n_scenarios):
        for c in range(n_cust):
            constraint_demand[c] = model.addCons((
                quicksum(x[c,p,d,s] for d in days_per_customer_path[c][p] for p in paths_of_customer[c])
                + quicksum(o[c,e,d,s] for d in days_per_customer_dedicated_path[c][p] for e in dedicated_paths_of_customer[c])
                == demand[c][s], z[c]
            ), name="cons1_{}_{}".format(c,s))
        for l in range(n_legs):
            for d in range(n_days):
                constraint_capacity[l,d,s] = model.addCons((
                    quicksum(x[c,p,d,s] for d in day_for_leg_in_path[c][p] for p in paths_of_customer[c] for c in range(n_cust))
                    <= unit_size[l][d] * y[l][d]
                ), name="cons2_{}_{}_{}".format(l,d,s))

    return model