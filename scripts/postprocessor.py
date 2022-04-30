import pandas as pd
from matplotlib import pyplot as plt
import os

# 1) Input data for plotting related to names and colors
unit_to_TWh = 8760 / 1000  # from Gwa to TWh

# Dicitonary for renaming
# Interconnectors
el_exp = [
    'elec_exp_kaz-uzb',
    'elec_exp_uzb-kaz',
    'elec_exp_kaz-kgz',
    'elec_exp_kgz-kaz',
    'elec_exp_kgz-tjk',
    'elec_exp_tjk-kgz',
    'elec_exp_kgz-uzb',
    'elec_exp_uzb-kgz',
    'elec_exp_tjk-uzb',
    'elec_exp_uzb-tjk',
    ]

# Grouping technologies based on fuel
rename_tec = {
    "coal": ["coal_ppl", "coal_ppl_u"],
    "gas": ["gas_cc", "gas_ppl", "gas_ct"],
    "nuclear": ["nuc_lc", "nuc_hc"],
    "biomass": ["bio_ppl", "bio_istig"],
    "pumped hydro": ["turbine"],
    "reservoir hydro": ["turbine_dam", "hydro_lc", "hydro_hc"],
    "solar PV": ["solar_pv_ppl"],
    "wind": ["wind_ppl", "wind_ppf"],
    "import": ["elec_imp"],
    "export": el_exp,
}

# Color map for plots based on fuels/technologies
color_map = {
    "coal": "k",
    "gas": "tomato",
    "nuclear": "cyan",
    "biomass": "green",
    "pumped hydro": "steelblue",
    "reservoir hydro": "skyblue",
    "solar PV": "gold",
    "wind": "c",
    "import": "mediumpurple",
    "export": "violet",
}

# Nodes and countries
nodes = {
    "KAZ": "Kazakhstan",
    "KGZ": "Kyrgyzstan",
    "TJK": "Tajikistan",
    "TKM": "Turkmenistan",
    "UZB": "Uzbekistan",
    "all": "Central Asia",
}

# Fetching technology list
tec_list = []
for key, var in rename_tec.items():
    tec_list = tec_list + var
    

# A utility function for fetching data of a parameter or variable
def read_var(
    sc,
    variable,
    tec_list,
    time=["year"],
    node="all",
    year_col="year_act",
    rename_tec={},
    year_min=2020,
    year_max=2050,
    year_result=None,
    groupby="year",
):
    # Nodes
    if node == "all":
        node = [x for x in sc.set("node") if x != "World"]

    # Finding if variable is MESSAGEix parameter or not
    if variable in sc.par_list():
        value = "value"
    else:
        value = "lvl"
    # Fetching variable data
    if time:
        if variable in sc.par_list():
            df = sc.par(
                variable, {"node_loc": node, "technology": tec_list, "time": time}
            )
        else:
            df = sc.var(
                variable, {"node_loc": node, "technology": tec_list, "time": time}
            )
    else:
        if variable in sc.par_list():
            df = sc.par(variable, {"node_loc": node, "technology": tec_list})
        else:
            df = sc.var(variable, {"node_loc": node, "technology": tec_list})

    # Results for one year
    if year_result:
        df = df.loc[df[year_col] == year_result].copy()

    # Grouping
    if groupby == "year":
        df = df.groupby([year_col, "technology"]).sum()[[value]].reset_index()
    else:
        df = df.groupby(["time", "technology"]).sum()[[value]].reset_index()

    # Pivot table
    df = df.pivot_table(index=year_col, columns="technology", values=value)
    df = df.fillna(0)

    # Renaming
    if rename_tec:
        d = pd.DataFrame(index=df.index)
        for key, val in rename_tec.items():
            d[key] = df.loc[:, df.columns.isin(val)].sum(axis=1)
        df = d.copy()

    # Choosing non-zero columns
    df = df.loc[:, (df != 0).any(axis=0)].copy()

    # Min maximum year
    if not year_result:
        df = df[(df.index <= year_max) & (df.index >= year_min)].copy()
    return df


def equal_pump(act, times):
    '''
    Equalizing extra act from pump and turbine in one time (balancing services)

    Parameters
    ----------
    act : DataFrame
        activity data.
    times : list
        sub-annual timelsices.
    '''
    for t in times:
        p = (act["time"] == t) & (act["technology"] == "pump")
        pu = act.loc[p, "lvl"]
        t = (act["time"] == t) & (act["technology"] == "turbine")
        tu = act.loc[t, "lvl"]
        if pu.empty:
            continue
        if float(pu) > 0 and float(tu) > 0:
            if float(tu) > float(pu):
                act.loc[t, "lvl"] -= float(act.loc[p, "lvl"])
                act.loc[p, "lvl"] = 0
            else:
                act.loc[p, "lvl"] -= float(act.loc[t, "lvl"])
                act.loc[t, "lvl"] = 0
    return act


def monthly_plot(sc, path, node="TJK", yr=2050, pumped_hydro=True):
    '''
    Input data for the plotting related to node selection for PHS
    '''
    if node not in ["TJK", "KGZ"]:
        print("Notice: there is no pumped hydro or reservoir hydro in",
              "the slected node {}.".format(node))
    if node == "TJK":
        river = "amu"
    elif node == "KGZ":
        river = "siri"
    
    # Time slices
    times = [x for x in sc.set("time") if x != "year"]
    
    inflow_tecs = [x for x in sc.set("technology") if "inflow_up" in x and river in x]
    water_com = [x for x in sc.set("commodity") if "water-" in x and river in x]
    
    # Storage technology: 'hydro_dam': reservoir hydro, 'hydro_pump': pumped hydro
    if pumped_hydro:
        tec_li = ["turbine", "pump"] + inflow_tecs
    else:
        tec_li = ["turbine_dam"] + inflow_tecs


    # 1) Plotting activity of different technologies for water
    act = (
        sc.var(
            "ACT", {"node_loc": node, "technology": tec_li, "year_act": yr, "time": times}
        )
        .groupby(["time", "technology"])
        .sum()
        .reset_index()
    )

    fig = plt.figure("water")
    for tec in tec_li:
        y = act.loc[act["technology"] == tec, "lvl"]
        if "pump" in tec:
            y = -y
        if not y.empty:
            plt.step(times, y, label=tec, where="mid")
    
    # Laying demand on the same plot
    dem = sc.par(
        "demand", {"node": node, "commodity": water_com, "year": yr, "time": times}
    )
    plt.step(dem["time"], dem["value"], label="demand", where="mid")
    
    # Adding legend
    plt.legend(loc="upper right", ncol=2)
    plt.title("Water demand and activity of storage technologies in {}".format(yr))

    # 2) Plotting for energy
    # Loading activity from the model
    act = (
        sc.var(
            "ACT",
            {
                "node_loc": node,
                "technology": tec_list + ["pump", "elec_t_d"] + el_exp,
                "year_act": yr,
                "time": times,
            },
        )
        .groupby(["time", "technology"])
        .sum()
        .reset_index()
    )
    act = equal_pump(act, times)
    act["time"] = [int(x) for x in act["time"]]
    act = act.sort_values(["time"])
    act["lvl"] *= unit_to_TWh

    fig = plt.figure("energy")
    for tec in rename_tec.keys():
        d = act.loc[act["technology"].isin(rename_tec[tec])].copy()
        if d.empty or d["lvl"].sum() < 0.00001:
            continue
        y = d.groupby("time").sum().reset_index()[["lvl"]]
        c = color_map[tec]
        if tec == "pumped hydro":
            tec = "PHS-discharge"
    
        # if tec == 'reservoir hydro':
        #     y['lvl'] = [0.5, 0.3, 0.7, 0.8, 1.5, 2, 1.6, 2.1, 1.8, 1.6, 1.4, 1]
        if tec == "export":
            y = -y
        plt.step(times, y, label=tec, where="mid", color=c)
    
    # For pump and exports with negative values
    y = act.loc[act["technology"] == "pump", "lvl"]
    plt.step(times, -y, label="PHS-charge", where="mid", color="red")
    
    # Laying demand on the same plot
    y = act.loc[act["technology"] == "elec_t_d", "lvl"]
    plt.step(dem.index, y, label="demand", where="mid", color="brown")

    # Adding legend
    ax = plt.gca()
    leg = ax.legend(
        loc="center right",
        facecolor="white",
        ncol=1,
        bbox_to_anchor=(1.35, 0.5),
        fontsize=9,
        framealpha=1,
    ).get_frame()
    leg.set_linewidth(1)
    leg.set_edgecolor("black")
    
    plt.title("Electricity demand and supply (TWh) in {} in {}".format(nodes[node], yr))
    plt.xlabel("Month of year")
    # Saving the file
    fig.savefig(path + "\\" + sc.scenario + "_" + "monthly_" + str(yr))
    
    # 3) A fig for electricity trade
    fig = plt.figure("trade")
    trade = pd.DataFrame(index=times, columns=pd.MultiIndex.from_product(
        [[x for x in nodes.keys() if x != "all"], ["Import", "Export"]],
        names=["Country", "Direction"]))
    for (node, direct) in trade.columns:
        if direct == "Import":
            tec_l = ["elec_imp"]
        else:
            tec_l = el_exp
        act = (
            sc.var(
                "ACT",
                {
                    "node_loc": node,
                    "technology": tec_l,
                    "year_act": yr,
                    "time": times,
                },
            )
            .groupby(["time"])
            .sum()
            .reset_index()
            )
        act["time"] = [int(x) for x in act["time"]]
        act = act.sort_values(["time"])
        act["lvl"] *= unit_to_TWh
        if direct == "Import":
            act["lvl"] *= -1
        trade.loc[:, (node, direct)] = act["lvl"].values
        
        plt.step(trade.index, act["lvl"].values, label=(node, direct), where="mid")
    
    # Adding legend
    ax = plt.gca()
    leg = ax.legend(
        loc="center right",
        facecolor="white",
        ncol=1,
        bbox_to_anchor=(1.35, 0.5),
        fontsize=9,
        framealpha=1,
    ).get_frame()
    leg.set_linewidth(1)
    leg.set_edgecolor("black")
    
    plt.title("Electricity trade (TWh) in {}".format(yr))
    plt.xlabel("Month of year")

# %%
def yearly_plot(sc, path, plot_type="activity", region="all",
                aggregate="all"):
    '''
    Plotting yearly values over multiple decades

    Parameters
    ----------
    sc : message_ix.Scenario
    activity: bool (default True)
        selection between plotting activity (True) or capacity (False)
    path: string (path)
        path to the folder for saving output files and figures
    region: list
        list of model regions to be visualized
    aggregate: string
        adding the aggregate of all regions
    '''
    # Check if solution exists
    if not sc.has_solution():
        print("Notice: the submitted scenario has no solution!!!")
        return []
    
    # Selection between activity and capacity
    if plot_type == "activity":
        variable = ["ACT", "activity"]
        ti = "year"
        tit = "Electricity generation mix"
        ylab = "TWh"
        if path:
            writer = pd.ExcelWriter(path + "\\activity.xlsx")
    else:
        variable = ["CAP", "capacity"]
        ti = None
        tit = "Total installed capacity"
        ylab = "GW"
        if path:
            writer = pd.ExcelWriter(path + "\\capacity.xlsx")
    
    dict_xls = {}
    
    # Regions
    if region == "all":
        region = [x for x in sc.set("node") if x not in ["World", "CAS"]]
    
    if aggregate:
        region = region + [aggregate]
    
    # Subplots
    height = int(len(region)) if len(region) % 2 != 0 else int(len(region)/2)
    breath = 1 if len(region) % 2 != 0 else 2
    fig, axes = plt.subplots(height, breath, figsize=(breath * 4, 3 * height))
    fig.subplots_adjust(bottom=0.15, wspace=0.3, hspace=0.5)

    if len(region) > 1:
        fig.suptitle(tit, fontweight="bold", position=(0.5, 0.95))
        axes = axes.reshape(-1)
    else:
        axes = [axes]
    f = 0
    for ax, node in zip(axes, region):
        f = f + 1
        # Loading activity
        d = read_var(sc, variable[0], tec_list, ti, node, "year_act", rename_tec)
        d.index.name = "Year"
        if plot_type == "activity":
            d *= unit_to_TWh
    
        # Making export with negative sign
        if "export" in d.columns:
            d["export"] = -d["export"]
        # Removing import/export from Central Asia as a whole
        if node == "all":
            d.loc[:, d.columns.isin(["import", "export"])] = 0
    
        # For writing to xls
        dict_xls[nodes[node]] = d
    
        # Plot
        d.plot(
            ax=ax,
            kind="bar",
            stacked=True,
            rot=0,
            width=0.7,
            color=color_map,
            edgecolor="k",
        )
    
        # Title and label
        ax.set_title(nodes[node], fontsize=11)
        ax.set_ylabel(ylab, fontsize=10)
        if f != len(region) and len(region) != 1:
            ax.get_legend().remove()
        # Adding a line at zero
        ax.axhline(0, color="black", linewidth=0.5)
    
    # legend
    if len(region) > 1:
        pos = (0.5, -0.55)
        leg = ax.legend(
            loc="center right",
            facecolor="white",
            ncol=3,
            bbox_to_anchor=pos,
            fontsize=9,
            framealpha=1,
        ).get_frame()
        leg.set_linewidth(1)
        leg.set_edgecolor("black")
    plt.show()
    
    # Saving the file
    fig.savefig(path + "\\" + sc.scenario + "_" + variable[1])

    # Saving xls file
    for sh in dict_xls.keys():
        df = dict_xls[sh]
        vre = [c for c in df.columns if c in ["wind", "solar PV"]]
        re = [
            c
            for c in df.columns
            if c in ["wind", "solar PV", "reservoir hydro", "pumped hydro"]
        ]
        df["share_vre"] = df[vre].sum(axis=1) / df.sum(axis=1)
        df["share_re"] = df[re].sum(axis=1) / df.sum(axis=1)
        df.to_excel(writer, sheet_name=sh)
    writer.save()
    writer.close()
    

def cost_emission_plot(sc, name="Baseline", max_yr=2055):
    '''
    Generate cost and emission plots.

    Parameters
    ----------
    sc : message_ix.Scenario
    name : string, optional
        Scenario name to be plotted. The default is "Baseline".
    max_yr : int, optional
        Maximum year to be shown in the plot. The default is 2055.

    '''
    tit = "Total costs and GHG emissions"
    
    # Retreiving CO2 emission factors
    df_cc = sc.par("relation_activity_time", {"relation": "CO2_cc"})
    df_cc = (
        df_cc.groupby(["technology", "year_act", "node_loc"])
        .sum()
        .drop(["year_rel"], axis=1)
        .sort_index()
    )
    # List of power plants
    tec_list = sc.par("output", {"commodity": "electr", "level": "secondary"})[
        "technology"
    ].unique()

    fig, axes = plt.subplots(2, 1, figsize=(9, 8))
    fig.subplots_adjust(bottom=0.15, wspace=0.3, hspace=0.5)
    fig.suptitle(tit, fontweight="bold", position=(0.5, 0.95))

    var_list = {
        "COST_NODAL_NET": "Total costs of energy system (million $/year)",
        "EMISS": "Total GHG emissions (MtCO2-eq/year)",
    }
    res = {}
    f = 0
    for ax, varname in zip(axes.reshape(-1), var_list.keys()):
        f = f + 1
    
        df_tot = pd.DataFrame()
        if "COST_NODAL_NET" in varname:
            df = sc.var(varname)
            yr_col = "year"
            node_col = "node"
            # Sorting and averaging
            df = df.loc[(df[yr_col] > 2015) &
                        (df[yr_col] < max_yr) &
                        (df[node_col].isin(nodes.keys()))].set_index(
                            [node_col, yr_col])["lvl"]
            if "NET" in varname:
                df *= 1000
        elif varname == "EMISS":
            df = sc.var(varname, {"emission": "TCE", "type_tec": "all"})
            df = sc.var("ACT", {"technology": tec_list, "time": "year"})
            yr_col = "year_act"
            node_col = "node_loc"

            # Sorting and averaging
            df = (
                df.loc[(df[yr_col] > 2015) &
                       (df[yr_col] < 2055) & (df[node_col].isin(nodes.keys()))]
                .groupby([node_col, "technology", yr_col])
                .sum()["lvl"]
            )
            df = (
                df.reset_index()
                .set_index(["technology", yr_col, node_col])
                .sort_index()
            )
            df = df.loc[df.index.isin(df_cc.index)].copy()
            df["lvl"] *= df_cc["value"]

            df["lvl"] = df["lvl"].fillna(0)
            df = df.reset_index().groupby([node_col, yr_col]).sum()
            df["lvl"] *= 44 / 12  # converting MtC to MtCO2

        df = df.unstack(yr_col).mean(axis=1)
        df_tot[name] = df
    
        # Total CAS
        df_tot.loc["all", :] = df_tot.sum(axis=0)
        df_tot.index = [nodes[x] for x in df_tot.index]
    
        # Plot
        df_tot.plot(ax=ax, kind="bar", stacked=False, rot=0, width=0.7, edgecolor="k")
        res[varname] = df_tot
        # Title and label
        ax.set_title(var_list[varname], fontsize=11)
        # ax.set_ylabel(ylab, fontsize=10)
        if f != len(nodes):
            ax.get_legend().remove()
        # Adding a line at zero
        ax.axhline(0, color="black", linewidth=0.5)
    
        # legend
        # pos = (1.15, 0.5)        # legend low = (1.65, 1.75)
        leg = ax.legend(
            loc="best",
            facecolor="white",
            ncol=1,
            # bbox_to_anchor=pos,
            fontsize=9,
            framealpha=1,
        ).get_frame()
        leg.set_linewidth(1)
        leg.set_edgecolor("black")
    plt.show()
    

def compare_three_scenario(sc_ref, sc1, sc2,
                           scenario_names=["Reference", "Scenario 1", "Scenario 2"],
                           ):
    '''
    Comparing different scenarios on some output variables (costs, emissions).
    Difference of scenario 1 and scenario 2 compared to reference.

    Parameters
    ----------
    sc_ref : message_ix.Scenario
        Reference scenario for comparison.
    sc1 : message_ix.Scenario
        First scenario to be compared.
    sc2 : message_ix.Scenario
        Second scenario to be compared. 
    scenario_names : list of strings
        Name of scenarios.
    '''
    
    tit = "Total costs and GHG emissions in different scenarios"
    var_list = {
        "COST_NODAL_NET": "Change in total costs of energy system (million $/year) relative to Baseline",
        "EMISS": "Change in total GHG emissions (MtCO2-eq/year) relative to Baseline",
       }
    
    # Making a dictionary of scenarios
    scenarios = {x:y for x,y in zip(scenario_names, [sc_ref, sc1, sc2])}
    
    # Reading emission factors from relations
    df_cc = sc1.par("relation_activity_time", {"relation": "CO2_cc"})
    df_cc = (
        df_cc.groupby(["technology", "year_act", "node_loc"])
        .sum()
        .drop(["year_rel"], axis=1)
        .sort_index()
    )
    # List of power plants
    tec_list = sc1.par("output", {"commodity": "electr", "level": "secondary"})[
        "technology"
        ].unique()
    fig, axes = plt.subplots(2, 1, figsize=(9, 8))
    fig.subplots_adjust(bottom=0.15, wspace=0.3, hspace=0.5)
    fig.suptitle(tit, fontweight="bold", position=(0.5, 0.95))
    f = 0
    
    # Collecting results in a loop
    res = {}
    for ax, varname in zip(axes.reshape(-1), var_list.keys()):
        f = f + 1
    
        df_tot = pd.DataFrame()
        for name, scen in scenarios.items():
            if "COST_NODAL_NET" in varname:
                df = scen.var(varname)
                yr_col = "year"
                node_col = "node"
                # Sorting and averaging
                df = df.loc[(df[yr_col] > 2015) &
                            (df[yr_col] < 2055) &
                            (df[node_col].isin(nodes.keys()))].set_index(
                                [node_col, yr_col])["lvl"]
                if "NET" in varname:
                    df *= 1000
            elif varname == "EMISS":
                df = scen.var(varname, {"emission": "TCE", "type_tec": "all"})
                df = scen.var("ACT", {"technology": tec_list, "time": "year"})
                yr_col = "year_act"
                node_col = "node_loc"
                # Sorting and averaging
                df = (
                    df.loc[(df[yr_col] > 2015) &
                           (df[yr_col] < 2055) & (df[node_col].isin(nodes.keys()))]
                    .groupby([node_col, "technology", yr_col])
                    .sum()["lvl"]
                )
                df = (
                    df.reset_index()
                    .set_index(["technology", yr_col, node_col])
                    .sort_index()
                )
                df = df.loc[df.index.isin(df_cc.index)].copy()
                df["lvl"] *= df_cc["value"]
    
                df["lvl"] = df["lvl"].fillna(0)
                df = df.reset_index().groupby([node_col, yr_col]).sum()
                df["lvl"] *= 44 / 12  # converting MtC to MtCO2
    
            df = df.unstack(yr_col).mean(axis=1)
            df_tot[name] = df
    
        # Total CAS
        df_tot.loc["all", :] = df_tot.sum(axis=0)
        df_tot.index = [nodes[x] for x in df_tot.index]
        d = df_tot[scenario_names[0]].copy()
        for c in [scenario_names[1], scenario_names[2]]:
            df_tot.loc[:, c] -= d.values
        df_tot = df_tot.drop([scenario_names[0]], axis=1)
    
        # Plot
        df_tot.plot(ax=ax, kind="bar", stacked=False, rot=0, width=0.7, edgecolor="k")
        res[varname] = df_tot
        # Title and label
        ax.set_title(var_list[varname], fontsize=11)
        if f != len(nodes):
            ax.get_legend().remove()
        # Adding a line at zero
        ax.axhline(0, color="black", linewidth=0.5)
    
        # legend
        leg = ax.legend(
            loc="best",
            facecolor="white",
            ncol=1,
            # bbox_to_anchor=pos,
            fontsize=9,
            framealpha=1,
        ).get_frame()
        leg.set_linewidth(1)
        leg.set_edgecolor("black")
    plt.show()