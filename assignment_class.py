class ProblemData:
    def __init__(self, base_path="data_files/", customer_pattern="100", scenario_pattern="1"):
        self.base_path = base_path
        self.customer_pattern = customer_pattern
        self.scenario_pattern = scenario_pattern
        self.n_cust = int(self.customer_pattern)
        self.n_scenarios = int(self.scenario_pattern)

        self.exit_dict = self.read_customer_to_consolidation_data()
        self.access_dict = self.read_consolidation_to_customer_data()
        self.customer_dict = self.read_customers_data()
        self.legs_dict = self.read_legs_data()
        self.cargo_legs_dict = self.read_cargo_legs_data()
        self.scenario_dict = self.read_scenario_data()
        self.consolidation = self.read_consolidation_points_data()
        self.n_days = max(v["day"] for vv in self.cargo_legs_dict.values() for v in vv) + 5
        self.n_legs = len(self.legs_dict)

        self.capacity_cost = {}
        self.unit_size = {}
        self.prepare_leg_costs()

        self.scenarios_all = {}
        self.prepare_scenarios()

        self.paths_of_customer = {}
        self.dedicated_paths_of_customer = {}
        self.days_per_customer_path = {}
        self.days_per_customer_dedicated_path = {}
        self.day_for_leg_in_path = {}
        self.day_for_leg_in_dedicated_path = {}
        self.path_cost = {}
        self.dedicated_path_cost = {}
        self.build_all_paths()

    def read_file(self, file):
        return open(self.base_path + file)

    def read_customer_to_consolidation_data(self):
        data = {}
        with self.read_file("cust_consol_moves.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                line_data = line.split(",")
                data[int(line_data[0]), line_data[1]] = {"travel_times": int(line_data[2]),"cost": int(line_data[3])}
        return data

    def read_consolidation_to_customer_data(self):
        data = {}
        with self.read_file("consol_cust_moves.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                line_data = line.split(",")
                data[int(line_data[0]), line_data[1]] = {"travel_times": int(line_data[2]),"cost": int(line_data[3])}
        return data

    def read_consolidation_points_data(self):
        consolidation = []
        with self.read_file("consol_points.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                consolidation.append(line.strip())
        return consolidation

    def read_customers_data(self):
        data = {}
        with self.read_file("customers.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                line_data = line.split(",")
                data[int(line_data[0])] = {"pick-up_day": int(line_data[1]),"service": int(line_data[2]), "unit_revenue": int(line_data[3]), "dedicated_cost": int(line_data[4])}
        return data

    def read_legs_data(self):
        data = {}
        with self.read_file("legs.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                line_data = line.split(",")
                data[line_data[0], line_data[1]] = {"travel_times": int(line_data[2])}
        return data

    def read_cargo_legs_data(self):
        data = {}
        with self.read_file("passenger_cargo_legs.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                line_data = line.split(",")
                key = (line_data[0], line_data[1])
                item = {"day": int(line_data[2]), "block_cost": int(line_data[3]), "block_capacity": int(line_data[4]), "cargo_block_capacity": int(line_data[5])}
                data.setdefault(key, []).append(item)
        return data

    def read_scenario_data(self):
        import glob
        pattern = self.base_path + self.customer_pattern + "_custs_" + self.scenario_pattern + "*scens_cust_demand_scens.txt"
        files = glob.glob(pattern)
        scenario_dict = {}
        for file in files:
            # name_split = file.split("_")
            n_cust = self.n_cust
            n_scenarios = self.n_scenarios
            scenario_dict[n_cust, n_scenarios] = {}
            with open(file) as f:
                for cnt, line in enumerate(f):
                    if cnt == 0: continue
                    line_data = line.split(",")
                    scenario_dict[n_cust, n_scenarios][cnt-1] = {
                        "p": float(line_data[0]),
                        "d": [float(x) for x in line_data[1:]]
                    }
        return scenario_dict

    def cargo_at_day(self, cons_i, dest_i, depart_day):
        for option in self.cargo_legs_dict.get((cons_i, dest_i), []):
            if option["day"] == depart_day:
                return option
        return None

    def prepare_leg_costs(self):
        for leg_cnt, leg in enumerate(self.legs_dict):
            for alt in self.cargo_legs_dict.get(leg, []):
                self.capacity_cost[leg_cnt, alt["day"]] = alt["block_cost"]
                self.unit_size[leg_cnt, alt["day"]] = alt["block_capacity"]

    def prepare_scenarios(self):
        for (n_cust_scen, n_scenarios), scenario_info in self.scenario_dict.items():
            scenario_chance = [scenario_info[s]["p"] for s in range(n_scenarios)]
            demand = [[scenario_info[s]["d"][c] for s in range(n_scenarios)] for c in range(self.n_cust)]
            revenue = [self.customer_dict[c]["unit_revenue"] for c in range(self.n_cust)]
            self.scenarios_all[n_cust_scen, n_scenarios] = {
                "scenario_chance": scenario_chance,
                "demand": demand,
                "revenue": revenue
            }
    
    def build_dedicated_paths_for_pair(self, c, cons_i, dest_i):
        cust_to_origin = self.exit_dict[c, cons_i]
        dest_to_dest = self.access_dict[c, dest_i]
        leg = self.legs_dict[cons_i, dest_i]

        pd = self.customer_dict[c]["pick-up_day"]
        dd = pd + self.customer_dict[c]["service"]

        tt = cust_to_origin["travel_times"] + dest_to_dest["travel_times"] + leg["travel_times"]

        if pd + tt > dd:
            return None

        slack_times = dd - (pd + tt) + 1
        alternatives = []

        for d in range(pd + cust_to_origin["travel_times"], pd + cust_to_origin["travel_times"] + slack_times):
            # scheduled = self.cargo_at_day(cons_i, dest_i, d)
            # if not scheduled:
            #     return None
            arrival = d + leg["travel_times"] + dest_to_dest["travel_times"]
            alternatives.append({
                "origin": cons_i, "destination": dest_i,
                "departing_at": d - cust_to_origin["travel_times"],
                "arriving_at": arrival,
                "land_cost": cust_to_origin["cost"] + dest_to_dest["cost"],
                "air_block_cost": self.customer_dict[c]["dedicated_cost"],
                "leg_departure": d
            })
        return alternatives

    def build_paths_for_pair(self, c, cons_i, dest_i):
        cust_to_origin = self.exit_dict[c, cons_i]
        dest_to_dest = self.access_dict[c, dest_i]
        leg = self.legs_dict[cons_i, dest_i]

        pd = self.customer_dict[c]["pick-up_day"]
        dd = pd + self.customer_dict[c]["service"]

        tt = cust_to_origin["travel_times"] + dest_to_dest["travel_times"] + leg["travel_times"]

        if pd + tt > dd:
            return None

        slack_times = dd - (pd + tt) + 1
        alternatives = []

        for d in range(pd + cust_to_origin["travel_times"], pd + cust_to_origin["travel_times"] + slack_times):
            scheduled = self.cargo_at_day(cons_i, dest_i, d)
            if not scheduled:
                return None
            arrival = d + leg["travel_times"] + dest_to_dest["travel_times"]
            alternatives.append({
                "origin": cons_i, "destination": dest_i,
                "departing_at": d - cust_to_origin["travel_times"],
                "arriving_at": arrival,
                "land_cost": cust_to_origin["cost"] + dest_to_dest["cost"],
                "air_block_cost": scheduled["block_cost"],
                "block_cap": scheduled["block_capacity"],
                "air_cap_blocks": scheduled["cargo_block_capacity"],
                "leg_departure": d
            })
        return alternatives

    def build_all_paths(self):
        route_id = 0
        dedicated_route_id = 0
        for c in range(self.n_cust):
            self.paths_of_customer[c] = []
            self.dedicated_paths_of_customer[c] = []
            for cons_i in self.consolidation:
                if (c, cons_i) in self.exit_dict:
                    for dest_i in self.consolidation:
                        if (c, dest_i) in self.access_dict:
                            if (cons_i, dest_i) in self.legs_dict:
                                # this ain't working properly
                                alts = self.build_paths_for_pair(c, cons_i, dest_i)
                                if not alts:
                                    continue
                                self.path_cost[c, route_id] = alts[0]["air_block_cost"] + alts[0]["land_cost"]
                                self.days_per_customer_path[c, route_id] = [a["departing_at"] for a in alts]
                                for a in alts:
                                    self.paths_of_customer[c].append(route_id)
                                    self.day_for_leg_in_path[c, route_id, a["leg_departure"]] = [a["departing_at"] for a in alts]
                                route_id += 1
                                # dedicated paths
                                alts_2 = self.build_dedicated_paths_for_pair(c, cons_i, dest_i)
                                if not alts_2:
                                    continue
                                self.dedicated_path_cost[c, dedicated_route_id] = alts_2[0]["air_block_cost"] + alts_2[0]["land_cost"]
                                self.days_per_customer_dedicated_path[c, dedicated_route_id] = [a["departing_at"] for a in alts_2]
                                for a in alts_2:
                                    self.dedicated_paths_of_customer[c].append(dedicated_route_id)
                                    self.day_for_leg_in_dedicated_path[c, dedicated_route_id, a["leg_departure"]] = [a["departing_at"] for a in alts_2]
                                dedicated_route_id += 1
                    
    def stoch_FFP_stochastic_model(self):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}

        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                for p in self.paths_of_customer[c]:
                    for d in range(self.n_days):
                        x[c,p,d,s] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}_{}'.format(c,p,d,s))
        
        for l in range(self.n_legs):
            for d in range(self.n_days):
                y[l,d] = model.addVar(vtype='I', lb=0, name='y_{}_{}'.format(l,d))
        
        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                z[c,s] = model.addVar(vtype='C', lb=0, name='z_{}_{}'.format(c,s))
        
        model.setObjective(
            (
                # Revenue term
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["scenario_chance"][s]
                    * self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c, s]
                    for c in range(self.n_cust)
                    for s in range(self.n_scenarios)
                )
                # Capacity cost term
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in range(self.n_days)
                )
                # Path cost term
                - quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["scenario_chance"][s]
                    * self.path_cost.get((c, p), 0)
                    * x[c, p, d, s]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                    for s in range(self.n_scenarios)
                )
            ),
            sense="maximize"
        )
        
        constraint_demand = {}
        constraint_z_c = {}
        constraint_enabled_cap = {}
        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                constraint_demand[c,s] = model.addCons(z[c,s] <= self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s], name="cons1_{}_{}".format(c,s))
                constraint_z_c[c,s] = model.addCons( quicksum( x[c,p,d,s] for d in self.days_per_customer_path.get((c, p), []) for p in self.paths_of_customer.get(c, [])) == z[c,s], name="cons2_{}_{}".format(c,s) )
            for l in range(self.n_legs):
                for d in range(self.n_days):
                    # constraint_enabled_cap[l,d,s] = model.addCons(quicksum(x[c,p,d_bar,s] for d_bar in self.day_for_leg_in_path.get((c,p,d), []) for p in self.paths_of_customer.get(c, []) for c in range(self.n_cust)) <= self.unit_size[l,d]*y[l,d], name="cons3_{}_{}".format(l,d))
                    # TODO: change the get methods for existence checks to save memory
                    constraint_enabled_cap[l, d, s] = model.addCons(
                        quicksum(
                            x[c, p, d_bar, s]
                            for c in range(self.n_cust)
                            for p in self.paths_of_customer.get(c, [])
                            for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                        )
                        <= self.unit_size.get((l,d),0) * y[l, d],
                        name="cons3_{}_{}".format(l, d)
                    )
        
        return model
    
    def stoch_FFP_customer_commitment(self):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}
        o = {}

        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                for p in self.paths_of_customer.get(c, []):
                    for d in range(self.n_days):
                        x[c, p, d, s] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}_{s}')
                # shall we create all time-feasible combinations for dedicated_paths_of_customer?
                for e in self.dedicated_paths_of_customer.get(c, []):
                    for d in range(self.n_days):
                        o[c, e, d, s] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}_{s}')

        for l in range(self.n_legs):
            for d in range(self.n_days):
                y[l, d] = model.addVar(vtype='I', lb=0, name=f'y_{l}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["scenario_chance"][s]
                    * self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s]
                    for c in range(self.n_cust)
                    for s in range(self.n_scenarios)
                )
                # Capacity cost
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in range(self.n_days)
                )
                # Path cost
                - quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["scenario_chance"][s]
                    * self.path_cost.get((c, p), 0)
                    * x[c, p, d, s]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                    for s in range(self.n_scenarios)
                )
                # Dedicated path cost
                - quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["scenario_chance"][s]
                    * self.dedicated_path_cost.get((c, e), 0)
                    * o[c, e, d, s]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    for s in range(self.n_scenarios)
                )
            ),
            sense="maximize"
        )

        constraint_demand = {}
        constraint_z = {}
        constraint_capacity = {}

        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                # z <= demand
                # constraint_demand[c, s] = model.addCons(
                #     z[c, s] <= self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                #     name=f"cons1_{c}_{s}"
                # )
                # Flow conservation: z = x + o
                constraint_z[c, s] = model.addCons(
                    quicksum(x[c, p, d, s] for p in self.paths_of_customer.get(c, []) for d in self.days_per_customer_path.get((c, p), []))
                    + quicksum(o[c, e, d, s] for e in self.dedicated_paths_of_customer.get(c, []) for d in self.days_per_customer_dedicated_path.get((c, e), []))
                    == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                    name=f"cons2_{c}_{s}"
                )
            for l in range(self.n_legs):
                for d in range(self.n_days):
                    # Capacity constraints
                    constraint_capacity[l, d, s] = model.addCons(
                        quicksum(
                            x[c, p, d_bar, s]
                            for c in range(self.n_cust)
                            for p in self.paths_of_customer.get(c, [])
                            for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                        )
                        <= self.unit_size.get((l, d), 0) * y[l, d],
                        name=f"cons3_{l}_{d}_{s}"
                    )

        return model

test_object = ProblemData()
model = test_object.stoch_FFP_customer_commitment()
model.optimize()
obj_val_big = model.getObjVal()
print("end")