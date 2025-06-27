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

def read_consolidation_points_data(file="data_files/consol_points.txt"):
    consolidation = []
    with open(file) as f:
        cnt = 0
        for line in f:
            if cnt == 0:
                continue
            else:
                consolidation.append(line)
            cnt += 1
    return consolidation

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
                if (line_data[0], line_data[1]) not in cargo_legs_dict:
                    cargo_legs_dict[line_data[0], line_data[1]] = [{"day": int(line_data[2]), "block_cost": int(line_data[3]), "block_capacity": int(line_data[4]), "cargo_block_capacity": int(line_data[5])}]
                else:
                    cargo_legs_dict[line_data[0], line_data[1]].append({"day": int(line_data[2]), "block_cost": int(line_data[3]), "block_capacity": int(line_data[4]), "cargo_block_capacity": int(line_data[5])})
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

def cargo_at_day(cons_i, dest_i, depart_opportunity_day, cargo_data):
    options_list = cargo_data[cons_i, dest_i]
    for option in options_list:
        if option["day"] == depart_opportunity_day:
            return option
    return None

def build_paths_for_customer_consolidation_pair(cons_i, dest_i, cust_to_origin_consolidation, dest_consolidation_to_dest, customer, leg, cargo_data):

    cust_i_1_tt = cust_to_origin_consolidation["travel_times"]
    cust_i_3_tt = dest_consolidation_to_dest["travel_times"]

    cust_i_1_c = cust_to_origin_consolidation["cost"]
    cust_i_3_c = dest_consolidation_to_dest["cost"]

    cust_i_pd = customer["pick-up_day"]
    cust_i_dd = cust_i_pd + customer["service"]

    leg_tt = leg["travel_times"]

    tt = cust_i_1_tt + cust_i_3_tt + leg_tt

    if cust_i_pd + tt > cust_i_dd:
        return None
    else:
        slack_times = cust_i_dd - (cust_i_pd + tt) + 1
        alternatives = []
        for depart_opportunity_day in range(cust_i_pd + cust_i_1_tt, cust_i_pd + cust_i_1_tt + slack_times):
            scheduled_object = cargo_at_day(cons_i, dest_i, depart_opportunity_day, cargo_data)
            if scheduled_object == None:
                return None
            else:
                arrival_time = depart_opportunity_day + leg_tt + cust_i_3_tt
                alternatives.append({"origin": cons_i, "destination": dest_i, "departing_at": depart_opportunity_day - cust_i_1_tt, "arriving_at": arrival_time, "land_cost": cust_i_1_c + cust_i_3_c, "air_block_cost": scheduled_object["block_cost"], "block_cap": scheduled_object["block_capacity"], "air_cap_blocks": scheduled_object["cargo_block_capacity"], "leg_departure": depart_opportunity_day})
    return alternatives


def read_data():
    '''
    We read a txt file, outputs:
    n_scenarios ready!
    n_cust ready!
    n_days ready!
    n_legs <----- re-think this

    these are available in dict scenario_dict
    scenario_chance          # List[float] of length n_scenarios
    revenue                  # List[float] of length n_cust
    demand                   # List[List[float]] or 2D array: [n_cust][n_scenarios]


    capacity_cost            # List[List[float]] or 2D array: [n_legs][n_days]
    unit_size                # List[List[float]] or 2D array: [n_legs][n_days]

    path_cost                # List[List[float]] or 2D array: [n_cust][n_paths] ready!

    paths_of_customer        # Dict[int, List[int]] ready!
    days_per_customer_path   # Dict[int, Dict[int, List[int]]] ready!
    day_for_leg_in_path      # Dict[int, Dict[int, List[int]]] 
    '''
    exit_dict = read_customer_to_consolidation_data()
    access_dict = read_consolidation_to_customer_data()
    customer_dict = read_customers_data()
    legs_dict = read_legs_data()
    cargo_legs_dict = read_cargo_legs_data()
    scenario_dict = read_scenario_data()
    consolidation = read_consolidation_points_data()

    n_cust = len(customer_dict)

    n_days = max(v["day"] for v in cargo_legs_dict.values()) + 5  # assuming days start at 0

    n_legs = len(legs_dict)
    legs_list = list(legs_dict.keys())

    capacity_cost = {}
    unit_size = {}
    leg_cnt = 0
    for leg in legs_list:
        capacity_cost[leg_cnt] = {}
        for alternative in cargo_legs_dict[leg]:
            # assuming it's unique
            capacity_cost[leg_cnt, alternative["day"]] = alternative["block_cost"]
            unit_size[leg_cnt, alternative["day"]] = alternative["block_capacity"]


    scenarios_all = {}
    for realisation in scenario_dict:
        (n_cust_scen, n_scenarios) = realisation
        scenario_info = scenario_dict[realisation]

        scenario_chance = [scenario_info[s]["p"] for s in range(n_scenarios)]
        demand = [[scenario_info[s]["d"][c] for s in range(n_scenarios)] for c in range(n_cust)]

        revenue = [customer_dict[c]["unit_revenue"] for c in range(n_cust)]
        scenarios_all[realisation] = {
            "scenario_chance": scenario_chance,
            "demand": demand,
            "revenue": revenue
        }

    # paths
    path_cost = {}
    days_per_customer_path = {}
    # a list of dates in which customer c can depart using path p, such that the leg used in the path is taken on \bar{day}
    day_for_leg_in_path = {}
    paths_of_customer = {}
    route_id = 0
    for c in range(n_cust):
        path_cost[c] = []
        # days_per_customer_path[c] = []
        paths_of_customer[c] = []
        customer = customer_dict[c]
        for cons_i in consolidation:
            if (c, cons_i) in exit_dict:
                cust_to_origin_consolidation = exit_dict[c, cons_i]
                for dest_i in consolidation:
                    if (dest_i, c) in access_dict:
                        dest_consolidation_to_dest = access_dict[c, dest_i]
                        leg = legs_dict[cons_i, dest_i]
                        alternatives = build_paths_for_customer_consolidation_pair(cons_i, dest_i, cust_to_origin_consolidation, dest_consolidation_to_dest, customer, leg, cargo_legs_dict)
                        if alternatives != None:
                            # assuming unique
                            path_cost[c, route_id] = [alternatives[i]["air_block_cost"] + alternatives[i]["land_cost"] for i in range(len(alternatives))]
                            # assuming unique
                            days_per_customer_path[c, route_id] = [alternatives[i]["departing_at"] for i in range(len(alternatives))]
                            for alt in alternatives:
                                paths_of_customer[c].append(route_id)
                                # assuming unique
                                day_for_leg_in_path[c, route_id, alt["leg_departure"]] = [alternatives[i]["departing_at"] for i in range(len(alternatives))]
                                route_id += 1
                                


    return paths_of_customer, days_per_customer_path, n_scenarios, n_cust, n_days, n_legs, scenario_chance, revenue, capacity_cost, path_cost, demand, day_for_leg_in_path, unit_size

def stoch_FFP_stochastic_model():
    from pyscipopt import Model, quicksum
    model = Model()

    x = {}
    y = {}
    z = {}

    for s in range(n_scenarios):
        for c in range(n_cust):
            for p in paths_of_customer[c]:
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
        - quicksum(capacity_cost.get((l, d), 0) * y[l,d] for l in range(n_legs) for d in range(n_days))
        - quicksum(scenario_chance[s] * path_cost.get((c, p), 0) * x[c,p,d,s] for d in days_per_customer_path.get((c, p), []) for p in paths_of_customer.get(c, []) for c in range(n_cust) for s in range(n_scenarios))
        ), sense="maximize")
    
    constraint_demand = {}
    constraint_z_c = {}
    constraint_enabled_cap = {}
    for s in range(n_scenarios):
        for c in range(n_cust):
            constraint_demand[c,s] = model.addCons(z[c,s] <= demand[c][s], name="cons1_{}_{}".format(c,s))
            constraint_z_c[c,s] = model.addCons( quicksum( x[c,p,d,s] for d in days_per_customer_path.get((c, p), []) for p in paths_of_customer.get(c, [])) == z[c,s], name="cons2_{}_{}".format(c,s) )
        for l in range(n_legs):
            for d in range(n_days):
                constraint_enabled_cap[l,d,s] = model.addCons(quicksum(x[c,p,d_bar,s] for d_bar in day_for_leg_in_path.get((c,p,d), []) for p in paths_of_customer.get(c, []) for c in range(n_cust)) <= unit_size[l,d]*y[l,d], name="cons3_{}_{}".format(l,d))
    
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