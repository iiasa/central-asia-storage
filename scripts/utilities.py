from itertools import product

def add_share_activity(sc, relation, tec_share, tec_total, shares, regions,
                       remove_old=True,
                       bounds=[("relation_lower_time", 0)],
                       parname="relation_activity_time"):
    '''
    Adds share constraints through user-defined relations.

    Parameters
    ----------
    sc : message_ix.Scenario
    relation : string
        Name of relation.
    tec_share : list
        List of technologies forming the share.
    tec_total : list
        List of technologies forming the total.
    shares : dict
        Pair of year and share values, e.g., {2030: 0.2, 2050: 0.5}
    regions : list
        List of model regions that this share applies to.
    remove_old : bool, optional
        If this relation name exists, will be removed. The default is True.
    bounds : list, optional
        List of relation bound parameters and their values.
        The default is [("relation_lower_time", 0)].
    parname : string, optional
        Parameter of relations. The default is "relation_activity_time".

    '''
    if relation in set(sc.set("relation")) and remove_old:
        sc.remove_set("relation", relation)
    sc.add_set("relation", relation)  
    # If tec share in tec total
    tec_tot = [x for x in tec_total if x not in tec_share]
    tec_tot_share = [x for x in tec_total if x in tec_share]
    for yr, val in shares.items():
        # Total technologies Coefficient of total is (-)
        for tec, node in product(tec_tot, regions):
            # Check if technology has output in this node and year
            df = sc.par("output", {"node_loc": node, "technology": tec, "year_act": yr})
            if df.empty:
                continue
            else:
                mode = df["mode"][0]
            sc.add_par(parname,
                       [relation, node, yr, node, tec, yr, mode, "year"], -val, "-")
        # Share technologies
        for tec, node in product(tec_share, regions):
            # Check if technology has output in this node and year
            df = sc.par("output", {"node_loc": node, "technology": tec, "year_act": yr})
            if df.empty:
                continue
            else:
                mode = df["mode"][0]
                
            # If technology in "share" is in "total" too or not
            coefficient = 1 - val if tec in tec_tot_share else 1
            sc.add_par(parname,
                       [relation, node, yr, node, tec, yr, mode, "year"],
                       coefficient, "-")
        # Bound of relation
        for node, (bound, num) in product(regions, bounds):
            sc.add_par(bound, [relation, node, yr, "year"], num, "-")

