class ProblemData:
    def __init__(self, base_path="data_files/", sample_path="data_files/", customer_pattern="100", scenario_pattern="1"):
        self.base_path = base_path
        self.sample_path = sample_path
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
        self.leg_days = {}
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
        self.leg_in_path = {}
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
        leg_id = 0
        with self.read_file("legs.txt") as f:
            for cnt, line in enumerate(f):
                if cnt == 0: continue
                line_data = line.split(",")
                data[line_data[0], line_data[1]] = {"travel_times": int(line_data[2]), "id": leg_id}
                leg_id += 1
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
        pattern = self.sample_path + self.customer_pattern + "_custs_" + self.scenario_pattern + "*scens_cust_demand_rec_cost_scens.txt"
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
                        "d": [float(x) for x in line_data[1:n_cust + 1]],
                        "c": [float(x) for x in line_data[n_cust + 1:]]
                    }
        return scenario_dict

    def cargo_at_day(self, cons_i, dest_i, depart_day):
        for option in self.cargo_legs_dict.get((cons_i, dest_i), []):
            if option["day"] == depart_day:
                return option
        return None

    def prepare_leg_costs(self):
        for leg_cnt, leg in enumerate(self.legs_dict):
            self.leg_days[leg_cnt] = []
            for alt in self.cargo_legs_dict.get(leg, []):
                self.capacity_cost[leg_cnt, alt["day"]] = alt["block_cost"]
                self.unit_size[leg_cnt, alt["day"]] = alt["block_capacity"]
                self.leg_days[leg_cnt].append(alt["day"])

    def prepare_scenarios(self):
        for (n_cust_scen, n_scenarios), scenario_info in self.scenario_dict.items():
            scenario_chance = [scenario_info[s]["p"] for s in range(n_scenarios)]
            demand = [[scenario_info[s]["d"][c] for s in range(n_scenarios)] for c in range(self.n_cust)]
            averaged_demand = [sum([demand[c][s] * scenario_chance[s] for s in range(n_scenarios)]) for c in range(self.n_cust)]
            revenue = [self.customer_dict[c]["unit_revenue"] for c in range(self.n_cust)]
            cost = [[scenario_info[s]["c"][c] for s in range(n_scenarios)] for c in range(self.n_cust)]
            averaged_cost = [sum([cost[c][s] * scenario_chance[s] for s in range(n_scenarios)]) for c in range(self.n_cust)]
            self.scenarios_all[n_cust_scen, n_scenarios] = {
                "scenario_chance": scenario_chance,
                "demand": demand,
                "revenue": revenue,
                "cost": cost,
                "averaged_demand": averaged_demand,
                "averaged_cost": averaged_cost
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
                "leg_departure": d,
                "leg_id": leg["id"]
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
                                # self.path_cost[c, route_id] = alts[0]["air_block_cost"] + alts[0]["land_cost"]
                                self.path_cost[c, route_id] = alts[0]["land_cost"]
                                self.days_per_customer_path[c, route_id] = [a["departing_at"] for a in alts]
                                for a in alts:
                                    self.paths_of_customer[c].append(route_id)
                                    self.day_for_leg_in_path[c, route_id, a["leg_departure"]] = [a["departing_at"]]
                                    leg = a["leg_id"]
                                    self.leg_in_path[leg, route_id, c] = 1
                                route_id += 1
                                # dedicated paths
                                alts_2 = self.build_dedicated_paths_for_pair(c, cons_i, dest_i)
                                if not alts_2:
                                    continue
                                self.dedicated_path_cost[c, dedicated_route_id] = alts_2[0]["air_block_cost"] + alts_2[0]["land_cost"]
                                self.days_per_customer_dedicated_path[c, dedicated_route_id] = [a["departing_at"] for a in alts_2]
                                for a in alts_2:
                                    self.dedicated_paths_of_customer[c].append(dedicated_route_id)
                                    self.day_for_leg_in_dedicated_path[c, dedicated_route_id, a["leg_departure"]] = [a["departing_at"]]
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
                    for d in self.days_per_customer_path[c,p]:
                        x[c,p,d,s] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}_{}'.format(c,p,d,s))
        
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
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
                    for d in self.leg_days[l]
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
                constraint_z_c[c,s] = model.addCons( quicksum( 
                                                              x[c,p,d,s] 
                                                              for p in self.paths_of_customer.get(c, [])
                                                              for d in self.days_per_customer_path.get((c, p), []) 
                                                              ) == z[c,s], name="cons2_{}_{}".format(c,s) )
            for l in range(self.n_legs):
                for d in self.leg_days[l]:
                    constraint_enabled_cap[l, d, s] = model.addCons(
                        quicksum(
                            x[c, p, d_bar, s]
                            for c in range(self.n_cust)
                            for p in self.paths_of_customer.get(c, [])
                            for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                        )
                        <= self.unit_size.get((l,d),0) * y[l, d],
                        name="cons3_{}_{}_{}".format(l, d, s)
                    )
        
        return model
    
    def stoch_FFP_deterministic_model_stage_1(self):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}

        # for s in range(self.n_scenarios):
        for c in range(self.n_cust):
            for p in self.paths_of_customer[c]:
                for d in self.days_per_customer_path[c,p]:
                    x[c,p,d] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}'.format(c,p,d))
        
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                y[l,d] = model.addVar(vtype='I', lb=0, name='y_{}_{}'.format(l,d))
        
        # for s in range(self.n_scenarios):
        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='C', lb=0, name='z_{}'.format(c))
        
        model.setObjective(
            (
                # Revenue term
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c]
                    for c in range(self.n_cust)
                )
                # Capacity cost term
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in self.leg_days[l]
                )
                # Path cost term
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
            ),
            sense="maximize"
        )
        
        constraint_demand = {}
        constraint_z_c = {}
        constraint_enabled_cap = {}
        constraint_debug = {}
        for c in range(self.n_cust):
            constraint_demand[c] = model.addCons(z[c] <= self.scenarios_all[self.n_cust, self.n_scenarios]["averaged_demand"][c], name="cons1_{}".format(c))
            constraint_z_c[c] = model.addCons( quicksum( 
                                                        x[c,p,d]
                                                        for p in self.paths_of_customer.get(c, [])
                                                        for d in self.days_per_customer_path.get((c, p), [])
                                                        ) == z[c], name="cons2_{}".format(c) )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                constraint_enabled_cap[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l,d),0) * y[l, d],
                    name="cons3_{}_{}".format(l, d)
                )
        
        return model
    
    def stoch_FFP_deterministic_model_stage_2(self, y, s):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        z = {}

        # for s in range(self.n_scenarios):
        for c in range(self.n_cust):
            for p in self.paths_of_customer[c]:
                for d in self.days_per_customer_path[c,p]:
                    x[c,p,d] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}'.format(c,p,d))
        
        # for s in range(self.n_scenarios):
        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='C', lb=0, name='z_{}'.format(c))
        
        model.setObjective(
            (
                # Revenue term
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c]
                    for c in range(self.n_cust)
                )
                # Path cost term
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
            ),
            sense="maximize"
        )
        
        constraint_demand = {}
        constraint_z_c = {}
        constraint_enabled_cap = {}
        constraint_debug = {}
        for c in range(self.n_cust):
            constraint_demand[c] = model.addCons(z[c] <= self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s], name="cons1_{}".format(c))
            constraint_z_c[c] = model.addCons( quicksum( 
                                                        x[c,p,d]
                                                        for p in self.paths_of_customer.get(c, [])
                                                        for d in self.days_per_customer_path.get((c, p), [])
                                                        ) == z[c], name="cons2_{}".format(c) )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                constraint_enabled_cap[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l,d),0) * y[l, d],
                    name="cons3_{}_{}".format(l, d)
                )
        
        return model
    
    def stoch_FFP_deterministic_model_perfect_information(self, s):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}

        # for s in range(self.n_scenarios):
        for c in range(self.n_cust):
            for p in self.paths_of_customer[c]:
                for d in self.days_per_customer_path[c,p]:
                    x[c,p,d] = model.addVar(vtype='C', lb=0, name='x_{}_{}_{}'.format(c,p,d))
        
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                y[l,d] = model.addVar(vtype='I', lb=0, name='y_{}_{}'.format(l,d))
        
        # for s in range(self.n_scenarios):
        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='C', lb=0, name='z_{}'.format(c))
        
        model.setObjective(
            (
                # Revenue term
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c]
                    for c in range(self.n_cust)
                )
                # Capacity cost term
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in self.leg_days[l]
                )
                # Path cost term
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
            ),
            sense="maximize"
        )
        
        constraint_demand = {}
        constraint_z_c = {}
        constraint_enabled_cap = {}
        # constraint_debug = {}
        for c in range(self.n_cust):
            constraint_demand[c] = model.addCons(z[c] <= self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s], name="cons1_{}".format(c))
            constraint_z_c[c] = model.addCons( quicksum( 
                                                        x[c,p,d]
                                                        for p in self.paths_of_customer.get(c, [])
                                                        for d in self.days_per_customer_path.get((c, p), [])
                                                        ) == z[c], name="cons2_{}".format(c) )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                constraint_enabled_cap[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
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
                    for d in self.days_per_customer_path[c,p]:
                        x[c, p, d, s] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}_{s}')
                # shall we create all time-feasible combinations for dedicated_paths_of_customer?
                for e in self.dedicated_paths_of_customer.get(c, []):
                    for d in self.days_per_customer_dedicated_path[c,e]:
                        o[c, e, d, s] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}_{s}')

        for l in range(self.n_legs):
            for d in self.leg_days[l]:
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
                    for d in self.leg_days[l]
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
        constraint_z = {}
        constraint_capacity = {}

        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                # Flow conservation: z = x + o
                constraint_z[c, s] = model.addCons(
                    quicksum(
                        x[c, p, d, s] 
                        for p in self.paths_of_customer.get(c, []) 
                        for d in self.days_per_customer_path.get((c, p), [])
                        )
                    + quicksum(
                        o[c, e, d, s] 
                        for e in self.dedicated_paths_of_customer.get(c, []) 
                        for d in self.days_per_customer_dedicated_path.get((c, e), [])
                        )
                    == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                    name=f"cons2_{c}_{s}"
                )
            for l in range(self.n_legs):
                for d in self.leg_days[l]:
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
    
    def stoch_FFP_customer_commitment_deterministic_model_stage_1(self):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}
        o = {}

        for c in range(self.n_cust):
            for p in self.paths_of_customer.get(c, []):
                for d in self.days_per_customer_path[c,p]:
                    x[c, p, d] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}')
            # shall we create all time-feasible combinations for dedicated_paths_of_customer?
            for e in self.dedicated_paths_of_customer.get(c, []):
                for d in self.days_per_customer_dedicated_path[c,e]:
                    o[c, e, d] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}')

        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                y[l, d] = model.addVar(vtype='I', lb=0, name=f'y_{l}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["averaged_demand"][c]
                    for c in range(self.n_cust)
                )
                # Capacity cost
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in self.leg_days[l]
                )
                # Path cost
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
                # Dedicated path cost
                - quicksum(
                    self.dedicated_path_cost.get((c, e), 0)
                    * o[c, e, d]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                )
            ),
            sense="maximize"
        )
        constraint_z = {}
        constraint_capacity = {}

        for c in range(self.n_cust):
            # Flow conservation: z = x + o
            constraint_z[c] = model.addCons(
                quicksum(
                    x[c, p, d] 
                    for p in self.paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_path.get((c, p), [])
                    )
                + quicksum(
                    o[c, e, d] 
                    for e in self.dedicated_paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    )
                == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["averaged_demand"][c],
                name=f"cons2_{c}"
            )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                # Capacity constraints
                constraint_capacity[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l, d), 0) * y[l, d],
                    name=f"cons3_{l}_{d}"
                )

        return model
    
    def stoch_FFP_customer_commitment_deterministic_model_stage_2(self, y, s):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        z = {}
        o = {}

        for c in range(self.n_cust):
            for p in self.paths_of_customer.get(c, []):
                for d in self.days_per_customer_path[c,p]:
                    x[c, p, d] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}')
            # shall we create all time-feasible combinations for dedicated_paths_of_customer?
            for e in self.dedicated_paths_of_customer.get(c, []):
                for d in self.days_per_customer_dedicated_path[c,e]:
                    o[c, e, d] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s]
                    for c in range(self.n_cust)
                )
                # Path cost
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
                # Dedicated path cost
                - quicksum(
                    self.dedicated_path_cost.get((c, e), 0)
                    * o[c, e, d]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                )
            ),
            sense="maximize"
        )
        constraint_z = {}
        constraint_capacity = {}

        for c in range(self.n_cust):
            # Flow conservation: z = x + o
            constraint_z[c] = model.addCons(
                quicksum(
                    x[c, p, d] 
                    for p in self.paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_path.get((c, p), [])
                    )
                + quicksum(
                    o[c, e, d] 
                    for e in self.dedicated_paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    )
                == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                name=f"cons2_{c}"
            )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                # Capacity constraints
                constraint_capacity[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l, d), 0) * y[l, d],
                    name=f"cons3_{l}_{d}"
                )

        return model
    
    def stoch_FFP_customer_commitment_deterministic_model_perfect_information(self, s):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}
        o = {}

        for c in range(self.n_cust):
            for p in self.paths_of_customer.get(c, []):
                for d in self.days_per_customer_path[c,p]:
                    x[c, p, d] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}')
            # shall we create all time-feasible combinations for dedicated_paths_of_customer?
            for e in self.dedicated_paths_of_customer.get(c, []):
                for d in self.days_per_customer_dedicated_path[c,e]:
                    o[c, e, d] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}')

        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                y[l, d] = model.addVar(vtype='I', lb=0, name=f'y_{l}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s]
                    for c in range(self.n_cust)
                )
                # Capacity cost
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in self.leg_days[l]
                )
                # Path cost
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
                # Dedicated path cost
                - quicksum(
                    self.dedicated_path_cost.get((c, e), 0)
                    * o[c, e, d]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                )
            ),
            sense="maximize"
        )
        constraint_z = {}
        constraint_capacity = {}

        for c in range(self.n_cust):
            # Flow conservation: z = x + o
            constraint_z[c] = model.addCons(
                quicksum(
                    x[c, p, d] 
                    for p in self.paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_path.get((c, p), [])
                    )
                + quicksum(
                    o[c, e, d] 
                    for e in self.dedicated_paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    )
                == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                name=f"cons2_{c}"
            )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                # Capacity constraints
                constraint_capacity[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l, d), 0) * y[l, d],
                    name=f"cons3_{l}_{d}"
                )

        return model
    
    def stoch_FFP_dedicated_uncertainty(self):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}
        o = {}

        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                for p in self.paths_of_customer.get(c, []):
                    for d in self.days_per_customer_path[c,p]:
                        x[c, p, d, s] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}_{s}')
                # shall we create all time-feasible combinations for dedicated_paths_of_customer?
                for e in self.dedicated_paths_of_customer.get(c, []):
                    for d in self.days_per_customer_dedicated_path[c,e]:
                        o[c, e, d, s] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}_{s}')

        for l in range(self.n_legs):
            for d in self.leg_days[l]:
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
                    for d in self.leg_days[l]
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
                    * self.scenario_dict[self.n_cust, self.n_scenarios][s]["c"][c]
                    * o[c, e, d, s]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    for s in range(self.n_scenarios)
                )
            ),
            sense="maximize"
        )
        
        constraint_z = {}
        constraint_capacity = {}

        for s in range(self.n_scenarios):
            for c in range(self.n_cust):
                # Flow conservation: z = x + o
                constraint_z[c, s] = model.addCons(
                    quicksum(
                        x[c, p, d, s] 
                        for p in self.paths_of_customer.get(c, []) 
                        for d in self.days_per_customer_path.get((c, p), [])
                        )
                    + quicksum(
                        o[c, e, d, s] 
                        for e in self.dedicated_paths_of_customer.get(c, []) 
                        for d in self.days_per_customer_dedicated_path.get((c, e), [])
                        )
                    == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                    name=f"cons2_{c}_{s}"
                )
            for l in range(self.n_legs):
                for d in self.leg_days[l]:
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
    
    def stoch_FFP_dedicated_uncertainty_deterministic_model_stage_1(self):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}
        o = {}

        for c in range(self.n_cust):
            for p in self.paths_of_customer.get(c, []):
                for d in self.days_per_customer_path[c,p]:
                    x[c, p, d] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}')
            # shall we create all time-feasible combinations for dedicated_paths_of_customer?
            for e in self.dedicated_paths_of_customer.get(c, []):
                for d in self.days_per_customer_dedicated_path[c,e]:
                    o[c, e, d] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}')

        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                y[l, d] = model.addVar(vtype='I', lb=0, name=f'y_{l}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["averaged_demand"][c]
                    for c in range(self.n_cust)
                )
                # Capacity cost
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in self.leg_days[l]
                )
                # Path cost
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
                # Dedicated path cost
                - quicksum(
                    quicksum(
                        self.scenarios_all[self.n_cust, self.n_scenarios]["scenario_chance"][s]
                        * self.scenario_dict[self.n_cust, self.n_scenarios][s]["c"][c]
                        for s in range(self.n_scenarios)
                    )
                    * o[c, e, d]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    
                )
            ),
            sense="maximize"
        )
        
        constraint_z = {}
        constraint_capacity = {}

        for c in range(self.n_cust):
            # Flow conservation: z = x + o
            constraint_z[c] = model.addCons(
                quicksum(
                    x[c, p, d] 
                    for p in self.paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_path.get((c, p), [])
                    )
                + quicksum(
                    o[c, e, d] 
                    for e in self.dedicated_paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    )
                == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["averaged_demand"][c],
                name=f"cons2_{c}"
            )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                # Capacity constraints
                constraint_capacity[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l, d), 0) * y[l, d],
                    name=f"cons3_{l}_{d}"
                )

        return model
    
    def stoch_FFP_dedicated_uncertainty_deterministic_model_stage_2(self, y ,s):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        z = {}
        o = {}

        for c in range(self.n_cust):
            for p in self.paths_of_customer.get(c, []):
                for d in self.days_per_customer_path[c,p]:
                    x[c, p, d] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}')
            # shall we create all time-feasible combinations for dedicated_paths_of_customer?
            for e in self.dedicated_paths_of_customer.get(c, []):
                for d in self.days_per_customer_dedicated_path[c,e]:
                    o[c, e, d] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s]
                    for c in range(self.n_cust)
                )
                # Path cost
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
                # Dedicated path cost
                - quicksum(
                    self.scenario_dict[self.n_cust, self.n_scenarios][s]["c"][c]
                    * o[c, e, d]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    
                )
            ),
            sense="maximize"
        )
        
        constraint_z = {}
        constraint_capacity = {}

        for c in range(self.n_cust):
            # Flow conservation: z = x + o
            constraint_z[c] = model.addCons(
                quicksum(
                    x[c, p, d] 
                    for p in self.paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_path.get((c, p), [])
                    )
                + quicksum(
                    o[c, e, d] 
                    for e in self.dedicated_paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    )
                == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                name=f"cons2_{c}"
            )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                # Capacity constraints
                constraint_capacity[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l, d), 0) * y[l, d],
                    name=f"cons3_{l}_{d}"
                )

        return model
    
    def stoch_FFP_dedicated_uncertainty_deterministic_model_perfect_information(self, s):
        from pyscipopt import Model, quicksum
        model = Model()

        x = {}
        y = {}
        z = {}
        o = {}

        for c in range(self.n_cust):
            for p in self.paths_of_customer.get(c, []):
                for d in self.days_per_customer_path[c,p]:
                    x[c, p, d] = model.addVar(vtype='C', lb=0, name=f'x_{c}_{p}_{d}')
            # shall we create all time-feasible combinations for dedicated_paths_of_customer?
            for e in self.dedicated_paths_of_customer.get(c, []):
                for d in self.days_per_customer_dedicated_path[c,e]:
                    o[c, e, d] = model.addVar(vtype='C', lb=0, name=f'o_{c}_{e}_{d}')

        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                y[l, d] = model.addVar(vtype='I', lb=0, name=f'y_{l}_{d}')

        for c in range(self.n_cust):
            z[c] = model.addVar(vtype='B', lb=0, name=f'z_{c}')

        model.setObjective(
            (
                # Revenue
                quicksum(
                    self.scenarios_all[self.n_cust, self.n_scenarios]["revenue"][c]
                    * z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s]
                    for c in range(self.n_cust)
                )
                # Capacity cost
                - quicksum(
                    self.capacity_cost.get((l, d), 0) * y[l, d]
                    for l in range(self.n_legs)
                    for d in self.leg_days[l]
                )
                # Path cost
                - quicksum(
                    self.path_cost.get((c, p), 0)
                    * x[c, p, d]
                    for c in range(self.n_cust)
                    for p in self.paths_of_customer.get(c, [])
                    for d in self.days_per_customer_path.get((c, p), [])
                )
                # Dedicated path cost
                - quicksum(
                    self.scenario_dict[self.n_cust, self.n_scenarios][s]["c"][c]
                    * o[c, e, d]
                    for c in range(self.n_cust)
                    for e in self.dedicated_paths_of_customer.get(c, [])
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    
                )
            ),
            sense="maximize"
        )
        
        constraint_z = {}
        constraint_capacity = {}

        for c in range(self.n_cust):
            # Flow conservation: z = x + o
            constraint_z[c] = model.addCons(
                quicksum(
                    x[c, p, d] 
                    for p in self.paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_path.get((c, p), [])
                    )
                + quicksum(
                    o[c, e, d] 
                    for e in self.dedicated_paths_of_customer.get(c, []) 
                    for d in self.days_per_customer_dedicated_path.get((c, e), [])
                    )
                == z[c] * self.scenarios_all[self.n_cust, self.n_scenarios]["demand"][c][s],
                name=f"cons2_{c}"
            )
        for l in range(self.n_legs):
            for d in self.leg_days[l]:
                # Capacity constraints
                constraint_capacity[l, d] = model.addCons(
                    quicksum(
                        x[c, p, d_bar]
                        for c in range(self.n_cust)
                        for p in self.paths_of_customer.get(c, [])
                        for d_bar in self.day_for_leg_in_path.get((c, p, d), [])
                    )
                    <= self.unit_size.get((l, d), 0) * y[l, d],
                    name=f"cons3_{l}_{d}"
                )

        return model

# test_object = ProblemData(scenario_pattern="1")
# model = test_object.stoch_FFP_dedicated_uncertainty()
# model.optimize()
# print("end")

class ProblemManagement:
    def __init__(self):
        pass

    def run_model_in_stability(self, stop_condition, model_name, step_scens_list = [1,5,10,25,50,75,100,250,500,750], m_size=5):
        import os
        from statistics import mean, stdev
        

        id_scenarios = 0
        n_scenarios = -1
        condition = stop_condition*100
        while condition > stop_condition:
            n_scenarios = step_scens_list[id_scenarios]
            id_scenarios += 1
            objectives = []
            for m in range(m_size):
                if os.path.isfile(str(100) + '_custs_' + str(n_scenarios) + '_sampleM_' + str(m) + '_scens_cust_demand_rec_cost_scens.txt'):
                    pass
                else:
                    os.system('python make_rc_scens_jp.py 100 {} {}'.format(n_scenarios,m))
                data_object = ProblemData("data_files/","jp_instances/", customer_pattern="100", scenario_pattern=str(n_scenarios))
                if model_name == "stoch_FFP_stochastic_model":
                    model = data_object.stoch_FFP_stochastic_model()
                elif model_name == "stoch_FFP_customer_commitment":
                    model = data_object.stoch_FFP_customer_commitment()
                elif model_name == "stoch_FFP_dedicated_uncertainty":
                    model = data_object.stoch_FFP_dedicated_uncertainty()
                else:
                    # TODO: raise error
                    print("not supported model")
                # revenue_dict, scenarios_dict, capacity = read_data("folder/{}_{}.txt".format(m,n_scenarios))
                # model=stochastic_knapsack_stochastic_model(len(revenue_dict.keys()), revenue_dict, penalize_by, scenarios_dict, len(scenarios_dict.keys()), capacity)
                model.optimize()
                obj_val = model.getObjVal()
                objectives.append(obj_val)
            differences = []
            for i in range(len(objectives)):
                for j in range(i, len(objectives)):
                    if i != j:
                        differences.append(abs(objectives[i] - objectives[j]))
            avg = mean(differences)
            sd = stdev(differences)
            # condition = sd/avg
            condition = avg
        return n_scenarios
    
    def run_model_out_stability(self, stop_condition, model_name, step_scens_list = [1,5,10,25,50,75,100,250,500,750], m_size=1, big_scenario=1000):
        import os
        from statistics import mean, stdev


        # os.system('python make_knapsack_data.py 20 100 1000 >> folder/big_instance.txt')
        data_object_big = ProblemData("data_files/","data_files/", customer_pattern="100", scenario_pattern=str(1000))
        if model_name == "stoch_FFP_stochastic_model":
            model_big = data_object_big.stoch_FFP_stochastic_model()
        elif model_name == "stoch_FFP_customer_commitment":
            model_big = data_object_big.stoch_FFP_customer_commitment()
        elif model_name == "stoch_FFP_dedicated_uncertainty":
            model_big = data_object_big.stoch_FFP_dedicated_uncertainty()
        else:
            # TODO: raise error
            print("not supported model")
        model_big.optimize()
        obj_val_big = model_big.getObjVal()
        
        id_scenarios = 0
        n_scenarios = -1
        condition = stop_condition*100
        while condition > stop_condition:
            n_scenarios = step_scens_list[id_scenarios]
            id_scenarios += 1
            objectives = []
            for m in range(m_size):
                if os.path.isfile(str(100) + '_custs_' + str(n_scenarios) + '_sampleM_' + str(m) + '_scens_cust_demand_rec_cost_scens.txt'):
                    pass
                else:
                    os.system('python make_rc_scens_jp.py 100 {} {}'.format(n_scenarios,m))
                data_object = ProblemData("data_files/","jp_instances/", customer_pattern="100", scenario_pattern=str(n_scenarios))
                if model_name == "stoch_FFP_stochastic_model":
                    model = data_object.stoch_FFP_stochastic_model()
                elif model_name == "stoch_FFP_customer_commitment":
                    model = data_object.stoch_FFP_customer_commitment()
                elif model_name == "stoch_FFP_dedicated_uncertainty":
                    model = data_object.stoch_FFP_dedicated_uncertainty()
                else:
                    # TODO: raise error
                    print("not supported model")
                # revenue_dict, scenarios_dict, capacity = read_data("folder/{}_{}.txt".format(m,n_scenarios))
                # model=stochastic_knapsack_stochastic_model(len(revenue_dict.keys()), revenue_dict, penalize_by, scenarios_dict, len(scenarios_dict.keys()), capacity)
                model.optimize()
                obj_val = model.getObjVal()
                objectives.append(obj_val)
            differences = []
            for i in range(len(objectives)):
                differences.append(abs(objectives[i] - obj_val_big))
            avg = mean(differences)
            sd = stdev(differences)
            # condition = sd/avg
            condition = avg
        return n_scenarios
    
    def run_deterministic_model(self, model_name, instance_cust, instance_scens):
        data_object = ProblemData("data_files/","data_files/", customer_pattern=str(instance_cust), scenario_pattern=str(instance_scens))
        
        v_det = 0
        model_stoch = data_object.stoch_FFP_stochastic_model()
        
        #1st stage: calculate fixed y
        if model_name == "stoch_FFP_stochastic_model":
            model_det_stage1 = data_object.stoch_FFP_deterministic_model_stage_1()
            # obtain 1st stage decision
            y = {}
            model_det_stage1.optimize()
            modelDet_st1_vars = model_det_stage1.getVars()
            for var in modelDet_st1_vars:
                if var.name[0] == "y":
                    _, l, d = var.name.split("_")
                    y[int(l), int(d)] = round(float(model_det_stage1.getVal(var)))
            
            v_det += sum([-y[l,d] * data_object.capacity_cost[l,d] for l in range(data_object.n_legs) for d in data_object.leg_days[l]])
            # call stage 2:
            for s in range(data_object.n_scenarios):
                model_stage2 = data_object.stoch_FFP_deterministic_model_stage_1(y, s)
                model_stage2.optimize()
                v_det += model_stage2.getObjVal() * data_object.scenarios_all[data_object.n_cust, data_object.n_scenarios]["scenario_chance"][s]
        elif model_name == "stoch_FFP_customer_commitment":
            model_det_stage1 = data_object.stoch_FFP_customer_commitment_deterministic_model_stage_1()
            # obtain 1st stage decision
            y = {}
            model_det_stage1.optimize()
            modelDet_st1_vars = model_det_stage1.getVars()
            for var in modelDet_st1_vars:
                if var.name[0] == "y":
                    _, l, d = var.name.split("_")
                    y[int(l), int(d)] = round(float(model_det_stage1.getVal(var)))
            
            v_det += sum([-y[l,d] * data_object.capacity_cost[l,d] for l in range(data_object.n_legs) for d in data_object.leg_days[l]])
            # call stage 2:
            for s in range(data_object.n_scenarios):
                model_stage2 = data_object.stoch_FFP_customer_commitment_deterministic_model_stage_2(y, s)
                model_stage2.optimize()
                v_det += model_stage2.getObjVal() * data_object.scenarios_all[data_object.n_cust, data_object.n_scenarios]["scenario_chance"][s]
        elif model_name == "stoch_FFP_dedicated_uncertainty":
            model_det_stage1 = data_object.stoch_FFP_dedicated_uncertainty_deterministic_model_stage_1()
            # obtain 1st stage decision
            y = {}
            model_det_stage1.optimize()
            modelDet_st1_vars = model_det_stage1.getVars()
            for var in modelDet_st1_vars:
                if var.name[0] == "y":
                    _, l, d = var.name.split("_")
                    y[int(l), int(d)] = round(float(model_det_stage1.getVal(var)))
            
            v_det += sum([-y[l,d] * data_object.capacity_cost[l,d] for l in range(data_object.n_legs) for d in data_object.leg_days[l]])
            # call stage 2:
            for s in range(data_object.n_scenarios):
                model_stage2 = data_object.stoch_FFP_dedicated_uncertainty_deterministic_model_stage_2(y, s)
                model_stage2.optimize()
                v_det += model_stage2.getObjVal() * data_object.scenarios_all[data_object.n_cust, data_object.n_scenarios]["scenario_chance"][s]
        else:
            # TODO: raise error
            print("not supported model")
        
        # get first model
        model_stoch.optimize()
        v_sp = model_stoch.getObjVal()
        
        
        
        
        vss = v_det - v_sp
        print("pause")
    
    def run_perfect_information_model(self, model_name, instance_cust, instance_scens):
        data_object = ProblemData("data_files/","data_files/", customer_pattern=str(instance_cust), scenario_pattern=str(instance_scens))
        
        v_ws = 0
        #1st stage: calculate fixed y
        if model_name == "stoch_FFP_stochastic_model":
            for s in range(data_object.n_scenarios):
                model_pi = data_object.stoch_FFP_deterministic_model_perfect_information(s)
                model_pi.optimize()
                v_ws += model_pi.getObjVal() * data_object.scenarios_all[data_object.n_cust, data_object.n_scenarios]["scenario_chance"][s]
            model_stoch = data_object.stoch_FFP_stochastic_model()
        elif model_name == "stoch_FFP_customer_commitment":
            for s in range(data_object.n_scenarios):
                model_pi = data_object.stoch_FFP_customer_commitment_deterministic_model_perfect_information(s)
                model_pi.optimize()
                v_ws += model_pi.getObjVal() * data_object.scenarios_all[data_object.n_cust, data_object.n_scenarios]["scenario_chance"][s]
            model_stoch = data_object.stoch_FFP_customer_commitment()
        elif model_name == "stoch_FFP_dedicated_uncertainty":
            for s in range(data_object.n_scenarios):
                model_pi = data_object.stoch_FFP_dedicated_uncertainty_deterministic_model_perfect_information(s)
                model_pi.optimize()
                v_ws += model_pi.getObjVal() * data_object.scenarios_all[data_object.n_cust, data_object.n_scenarios]["scenario_chance"][s]
            model_stoch = data_object.stoch_FFP_dedicated_uncertainty()
        else:
            # TODO: raise error
            print("not supported model")
        
        # get first model
        model_stoch.optimize()
        v_sp = model_stoch.getObjVal()
        
        
        evpi = v_sp - v_ws
        print("pause")
        
    
# test_object = ProblemManagement()
# test_object.run_model_out_stability(10, "stoch_FFP_stochastic_model", m_size=5)
# print("end")

test_object = ProblemManagement()
test_object.run_deterministic_model("stoch_FFP_customer_commitment", 100, 5)
print("end")