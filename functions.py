import pandas as pd
import data as d
import streamlit as st
import numpy as np
import numpy_financial as nf

from proforma_reforms import Reform_effects as Reforms

def initialize_game():
    st.title("Week 3 Developer Game")
    st.write("Welcome to week 3 of MAS.552!")
    st.write("This week, you will be playing as a developer, simulating the second stage of dynamic zoning.")
    st.write("Based on your votes last week with Propagational Voting, we have created a menu of amenity options that you can fund in your neighborhood, in exchange for more FAR (Floor Area Ratio) for your buildings.")
    st.write("You will be able to select up to 3 amenities to fund, and the more you fund, the more FAR you can build, and the more profit you can make.")
    st.write("Take into consideration both profit and what kind of developer you want to be, and the neighborhood you want to build.")
    st.write("Real estate development is both an art and a science, and you will need to balance both to succeed.")
    st.write("Good luck!")

def prev_week_results():
    st.write("Last week, here's how you voted:")
    st.write(d.pv_results)
    d.amenity_menu = FAR_bonus_menu()
    st.write("This generated the following menu for the developers to choose from:")
    st.write(d.amenity_menu)

def FAR_bonus(amenity_name, priority_weights):
    # Get the amenity row from the dataframe by filtering on the "Amenity" column
    amenity_row = d.amenity_menu[d.amenity_menu["Amenity"] == amenity_name].iloc[0]
    
    # Use Base_ constants so FAR bonus values stay stable across reruns,
    # even after proforma_inputs_updater mutates d.Building_Type / d.building_specs.
    apt_size = d.input_factors["Apt_size"]
    apt_cost = apt_size * d.construction_costs_noncore[d.Base_Building_Type]
    apt_NOI_annual = apt_size * (d.building_type_rent_upkeep.at[d.Base_Building_Type, "rent"] - d.building_type_rent_upkeep.at[d.Base_Building_Type, "upkeep"]) * 12
    
    # Apt_number_per_floor: how many apartments fit per floor (using original land plot size)
    apt_per_floor = d.Base_Buildable_Area / apt_size if apt_size != 0 else 0
    
    cost_equivalent = amenity_row["Cost"] / apt_cost if apt_cost != 0 else 0
    if amenity_row["Land Use"] == "Setback": #this is included because setbacks shave off square footage from all floors, not just the bottom floor
        sqft_equivalent = amenity_row["Square Footage"] / apt_size * d.maxheight_pre_bonus if apt_size != 0 else 0
    else:
        sqft_equivalent = amenity_row["Square Footage"] / apt_size if apt_size != 0 else 0
    rent_equivalent = (amenity_row["Annual Rent"] - amenity_row["Annual Upkeep"]) / apt_NOI_annual if apt_NOI_annual != 0 else 0
    
    FAR_Bonus_Add = (cost_equivalent + sqft_equivalent + rent_equivalent) / apt_per_floor if apt_per_floor != 0 else 0
    FAR_Bonus_Add *= priority_weights * d.FAR_Booster
    
    return FAR_Bonus_Add

def FAR_bonus_menu():
    # Create a copy to avoid modifying the original during iteration
    amenity_menu_copy = d.amenity_menu.copy()
    
    for idx, amenity_name in enumerate(d.amenity_menu["Amenity"]):
        priority_weight = d.pv_results[d.pv_results["Amenity"] == amenity_name]["Votes"].iloc[0]
        FAR_Bonus_Add = FAR_bonus(amenity_name, priority_weight)
        # Use the integer index to set the value
        amenity_menu_copy.at[idx, "FAR Bonus"] = FAR_Bonus_Add
    
    return amenity_menu_copy

def _calculate_far_bonus(amenity_counts_dict):
    """Calculate the total FAR bonus from a dict of {amenity_name: count}.
    Uses the same diminishing-returns scaling as the sidebar selection."""
    total = 0
    for name, count in amenity_counts_dict.items():
        if count == 0:
            continue
        rows = d.amenity_menu[d.amenity_menu["Amenity"] == name]
        if rows.empty:
            continue
        per_unit_bonus = rows.iloc[0]["FAR Bonus"]
        scaled_count = count if count <= 1 else np.log(count) + 1
        total += scaled_count * per_unit_bonus
    return total


def _marginal_far_bonus(amenity_name, current_count, per_unit_bonus):
    """FAR bonus from adding one more unit given current_count (diminishing returns)."""
    if current_count <= 0:
        scaled_current = 0
    elif current_count <= 1:
        scaled_current = current_count
    else:
        scaled_current = np.log(current_count) + 1
    next_count = current_count + 1
    scaled_next = next_count if next_count <= 1 else np.log(next_count) + 1
    return (scaled_next - scaled_current) * per_unit_bonus


def amenity_select_sidebar(is_round2=False):
    """Amenity selection sidebar. When is_round2=True, selection starts at 0 (independent per cycle)
    but FAR bonus uses cumulative counts for diminishing returns across cycles."""
    st.sidebar.title("Amenity Selection")
    st.sidebar.write("Select how many of each amenity you want to fund.")
    
    # Initialize session_state for committed amenity counts (round 1 results; used for FAR diminishing returns)
    if "amenity_counts_committed" not in st.session_state:
        st.session_state.amenity_counts_committed = {
            row["Amenity"]: 0 for _, row in d.amenity_menu.iterrows()
        }
    
    committed = st.session_state.amenity_counts_committed
    land_plot_size = d.input_factors["Land_plot_size"]
    setback_amenities = d.amenity_menu[d.amenity_menu["Land Use"] == "Setback"]
    
    if is_round2:
        # Show diminishing FAR benefits table: Round 1 count and marginal FAR (+1) per amenity
        marginal_rows = []
        for _, row in d.amenity_menu.iterrows():
            name = row["Amenity"]
            per_unit = row["FAR Bonus"]
            r1_count = committed.get(name, 0)
            marginal = _marginal_far_bonus(name, r1_count, per_unit)
            marginal_rows.append({
                "Amenity": name,
                "Round 1": r1_count,
                "Marginal FAR (+1)": round(marginal, 4),
            })
        marginal_df = pd.DataFrame(marginal_rows)
        st.sidebar.caption("Diminishing returns: FAR bonus per additional unit (given Round 1 choices)")
        st.sidebar.dataframe(marginal_df, use_container_width=True, hide_index=True)
        st.sidebar.divider()
    
    amenity_counts = {}
    for _, row in d.amenity_menu.iterrows():
        name = row["Amenity"]
        per_unit_bonus = row["FAR Bonus"]
        
        if is_round2:
            # Round 2: selection starts at 0, independent of round 1
            min_val = 0
            default_val = 0
            widget_key = f"amenity_round2_{name}"
            r1_count = committed.get(name, 0)
            marginal = _marginal_far_bonus(name, r1_count, per_unit_bonus)
            label = f"{name} (Round 1: {r1_count}, Marginal FAR: {round(marginal, 3)})"
        else:
            # Round 1: selection starts at 0 (committed is 0)
            min_val = committed.get(name, 0)
            default_val = min_val
            widget_key = f"amenity_{name}"
            label = f"{name} (FAR Bonus: {round(per_unit_bonus, 2)})"
        
        if row["Land Use"] == "Setback" and row["Square Footage"] > 0:
            # Other setback sqft = committed + current round selection (cumulative for space)
            other_setback_sqft = sum(
                (committed.get(other_name, 0) + amenity_counts.get(other_name, 0))
                * d.amenity_menu[d.amenity_menu["Amenity"] == other_name].iloc[0]["Square Footage"]
                for other_name in setback_amenities["Amenity"] if other_name != name
            )
            remaining_space = land_plot_size - other_setback_sqft
            max_count = max(min_val, int(remaining_space // row["Square Footage"]))
        else:
            max_count = 10
        
        count = st.sidebar.number_input(
            label,
            min_value=min_val, max_value=max_count, value=default_val, step=1, key=widget_key
        )
        amenity_counts[name] = count

    if is_round2:
        # Round 2: amenity_counts = this cycle only. FAR uses cumulative for diminishing returns.
        counts_this_round = amenity_counts.copy()
        counts_cumulative = {n: committed.get(n, 0) + counts_this_round.get(n, 0) for n in amenity_counts}
        total_FAR_Bonus = _calculate_far_bonus(counts_cumulative)
        committed_FAR_Bonus = _calculate_far_bonus(committed)
        incremental_FAR_Bonus = total_FAR_Bonus - committed_FAR_Bonus
        selected_this_round = [n for n, c in counts_this_round.items() if c > 0]
        selected_cumulative = [n for n, c in counts_cumulative.items() if c > 0]
        st.sidebar.write("Round FAR Bonus:", round(incremental_FAR_Bonus, 2))
        return total_FAR_Bonus, incremental_FAR_Bonus, selected_this_round, counts_this_round, selected_cumulative, counts_cumulative
    else:
        # Round 1: incremental == total (committed is 0)
        total_FAR_Bonus = _calculate_far_bonus(amenity_counts)
        incremental_FAR_Bonus = total_FAR_Bonus
        selected_amenities = [n for n, c in amenity_counts.items() if c > 0]
        st.sidebar.write("Round FAR Bonus:", round(incremental_FAR_Bonus, 2))
        return total_FAR_Bonus, incremental_FAR_Bonus, selected_amenities, amenity_counts, selected_amenities, amenity_counts



def amenity_select_main(total_FAR_bonus, selected_amenities, amenity_counts):
    # Build a table showing selected amenities with their quantities
    selected_rows = []
    for name in selected_amenities:
        row = d.amenity_menu[d.amenity_menu["Amenity"] == name].iloc[0].copy()
        count = amenity_counts[name]
        # Multiply numeric columns by count
        for col_name in row.index:
            if col_name not in ["Amenity", "Land Use"] and pd.api.types.is_numeric_dtype(type(row[col_name])):
                row[col_name] = row[col_name] * count
        selected_rows.append(row)

    if selected_rows:
        selected_menu = pd.DataFrame(selected_rows)
        # Add a total row: "Total" in Amenity, sum numeric columns, N/A for non-numeric
        total_row = {}
        for col in selected_menu.columns:
            if col == "Amenity":
                total_row[col] = "Total"
            elif pd.api.types.is_numeric_dtype(selected_menu[col]):
                total_row[col] = selected_menu[col].sum()
            else:
                total_row[col] = "N/A"
        selected_menu_with_total = pd.concat([selected_menu, pd.DataFrame([total_row])], ignore_index=True)
        st.write(selected_menu_with_total)
    else:
        st.write("No amenities selected.")

    st.write("**Round FAR Bonus:**", round(total_FAR_bonus, 2))


def proforma_inputs_updater(total_FAR_bonus, selected_amenities, amenity_counts):

    # === IMMEDIATE UPDATES (directly from inputs) ===

    # 1. Stories: total_FAR_bonus adds floors on top of the base height.
    #    Justification: the developer earns extra floors by funding amenities.
    d.building_specs["Stories"] = d.maxheight_pre_bonus + total_FAR_bonus

    # 2. Non-Buildable_Area: only selected setback amenities consume land,
    #    multiplied by how many of each were selected.
    #    Justification: setback amenities (e.g. Pocket Park) physically occupy part of
    #    the land plot on every floor, reducing the footprint available for building.
    setback_selected = d.amenity_menu[
        (d.amenity_menu["Land Use"] == "Setback") &
        (d.amenity_menu["Amenity"].isin(selected_amenities))
    ]
    d.building_specs["Non-Buildable_Area"] = sum(
        row["Square Footage"] * amenity_counts.get(row["Amenity"], 0)
        for _, row in setback_selected.iterrows()
    )

    # === DOWNSTREAM UPDATES (depend on the above) ===

    # 3. Buildable_Area: land plot minus setback area.
    #    Justification: whatever land the setbacks don't use is available to build on.
    d.building_specs["Buildable_Area"] = d.input_factors["Land_plot_size"] - d.building_specs["Non-Buildable_Area"]

    # Guard: avoid division by zero when setbacks consume the entire site
    buildable = d.building_specs["Buildable_Area"]

    # 4. Retail_floors: if Ramen Shop (On-Site retail) is selected, its square footage
    #    occupies a fraction of a floor.
    #    Justification: the Ramen Shop takes up ground-floor area proportional to its
    #    square footage relative to the buildable footprint.
    if "Ramen Shop" in selected_amenities and buildable > 0:
        ramen_row = d.amenity_menu[d.amenity_menu["Amenity"] == "Ramen Shop"].iloc[0]
        ramen_count = amenity_counts.get("Ramen Shop", 1)
        d.building_specs["Retail_floors"] = ramen_row["Square Footage"] * ramen_count / buildable
    else:
        d.building_specs["Retail_floors"] = 0

    # 4b. Subsidized_floors: if Subsidized Housing is selected, its square footage
    #     occupies a fraction of a floor per unit.
    #     Justification: each subsidized unit replaces market-rate residential space
    #     inside the building, so we carve it out to avoid double-counting rent.
    if "Subsidized Housing" in selected_amenities and buildable > 0:
        sub_row = d.amenity_menu[d.amenity_menu["Amenity"] == "Subsidized Housing"].iloc[0]
        sub_count = amenity_counts.get("Subsidized Housing", 1)
        d.building_specs["Subsidized_floors"] = sub_row["Square Footage"] * sub_count / buildable
    else:
        d.building_specs["Subsidized_floors"] = 0

    # 5. Residential_floors: total stories minus retail and subsidized floors.
    #    Justification: floors not used for retail or subsidized housing are market-rate residential.
    d.building_specs["Residential_floors"] = d.building_specs["Stories"] - d.building_specs["Retail_floors"] - d.building_specs["Subsidized_floors"]

    # 6. Rentable_area_residential: buildable footprint * residential floors (market-rate only).
    #    Justification: total leasable market-rate residential space across all residential floors.
    d.building_specs["Rentable_area_residential"] = d.building_specs["Buildable_Area"] * d.building_specs["Residential_floors"]

    # 7. Rentable_area_retail: buildable footprint * retail floors.
    #    Justification: total leasable retail space across all retail floors.
    d.building_specs["Rentable_area_retail"] = d.building_specs["Buildable_Area"] * d.building_specs["Retail_floors"]

    # 7b. Rentable_area_subsidized: buildable footprint * subsidized floors.
    #     Justification: total leasable subsidized residential space.
    d.building_specs["Rentable_area_subsidized"] = d.building_specs["Buildable_Area"] * d.building_specs["Subsidized_floors"]

    # 8. Building_Type: the number of stories determines cost/rent tier.
    #    Justification: taller buildings require more expensive construction methods
    #    (e.g. steel vs wood frame), so crossing a height threshold changes the type.
    if d.building_specs["Stories"] <= d.building_type_maxheight["Lowrise"]:
        d.Building_Type = "Lowrise"
    elif d.building_specs["Stories"] <= d.building_type_maxheight["Midrise_short"]:
        d.Building_Type = "Midrise_short"
    elif d.building_specs["Stories"] <= d.building_type_maxheight["Midrise_tall"]:
        d.Building_Type = "Midrise_tall"
    else:
        d.Building_Type = "Highrise"

    # 9. Retail rent/upkeep per sqft per month: if Ramen Shop is selected, derive
    #    from its annual financials.
    #    Justification: the Ramen Shop's Annual Rent and Annual Upkeep from amenity_menu
    #    are totals; we convert to per-sqft-per-month so the pro forma can use them
    #    consistently with residential rent/upkeep.
    if "Ramen Shop" in selected_amenities and d.building_specs["Rentable_area_retail"] != 0:
        ramen_row = d.amenity_menu[d.amenity_menu["Amenity"] == "Ramen Shop"].iloc[0]
        ramen_count = amenity_counts.get("Ramen Shop", 1)
        d.building_type_rent_upkeep.at["Retail_floors", "rent"] = ramen_row["Annual Rent"] * ramen_count / d.building_specs["Rentable_area_retail"] / 12
        d.building_type_rent_upkeep.at["Retail_floors", "upkeep"] = ramen_row["Annual Upkeep"] * ramen_count / d.building_specs["Rentable_area_retail"] / 12

    # 10. Construction_costs: depend on building type, rentable areas, and stories.
    #     Justification: construction cost per sqft varies by building type; total cost
    #     scales with the rentable area and number of stories. Must be recalculated
    #     because Stories, Buildable_Area, rentable areas, and Building_Type may all
    #     have changed above.
    d.Construction_Costs["Land"] = d.construction_costs_noncore["Land"] * d.input_factors["Land_plot_size"]
    d.Construction_Costs["Residential"] = d.construction_costs_noncore[d.Building_Type] * d.building_specs["Rentable_area_residential"]
    d.Construction_Costs["Retail"] = d.construction_costs_noncore[d.Building_Type] * d.building_specs["Rentable_area_retail"]
    d.Construction_Costs["Corridoor"] = d.construction_costs_noncore[d.Building_Type] * d.building_specs["Corridoor_size_per_floor"] * d.building_specs["Stories"]
    d.Construction_Costs["Elevator"] = d.construction_costs_core["Elevator"] * d.building_specs["Elevator_per_floor"] * d.building_specs["Stories"]
    d.Construction_Costs["Stairwell"] = d.construction_costs_core["Stairwell"] * d.building_specs["Stairwell_per_floor"] * d.building_specs["Stories"]
    d.Construction_Costs["Total"] = (d.Construction_Costs["Land"] + d.Construction_Costs["Residential"] + d.Construction_Costs["Retail"]
        + d.Construction_Costs["Corridoor"] + d.Construction_Costs["Elevator"] + d.Construction_Costs["Stairwell"])
    d.Construction_Costs["Total_ex_land"] = d.Construction_Costs["Total"] - d.Construction_Costs["Land"]

    # 11. Amenity costs: sum of one-time costs for all selected amenities, multiplied
    #     by count.
    #     Justification: the developer pays for the amenities they chose; this is an
    #     additional hard cost that feeds into the pro forma.
    amenity_selected = d.amenity_menu[d.amenity_menu["Amenity"].isin(selected_amenities)]
    d.Construction_Costs["Amenities"] = sum(
        row["Cost"] * amenity_counts.get(row["Amenity"], 0)
        for _, row in amenity_selected.iterrows()
    )

#==========================================
#PRO FORMA CALCULATIONS

d.misc_items["Years of Delay"] += Reforms["Delays Changes"]

#NOTE: need to redo the calculations for the floors of mixed use.


ProForma_Table = pd.DataFrame(
    index=["Rent", "Hard Costs", "Soft Costs", "Land Costs", "Upkeep", "Net Operating Income", "Other Expenses", "Debt Inflow/Outflow", "Remaining Debt", "Property Sold Inflow", "Pre-Tax Cash Flow"],
    columns=range(d.misc_items["Periods"]+2)
)

def Property_Sell_value(final_period):
    return ProForma_Table.at["Net Operating Income", final_period + 1] * d.misc_items["Exit Value Multiple"]

def Core_and_Corridoor_Upkeep():
    # Annual upkeep for elevators, stairwells, and corridoors (already in construction costs, but upkeep is recurring)
    # Uses d. references so values reflect proforma_inputs_updater changes
    elevator = d.building_type_rent_upkeep.at["Elevator", "upkeep"] * d.building_specs["Elevator_per_floor"] * (1 + Reforms["Elevator Upkeep"])
    stairwell = d.building_type_rent_upkeep.at["Stairwell", "upkeep"] * d.building_specs["Stairwell_per_floor"] * (1 + Reforms["Stairwell Upkeep"])
    corridoor = d.building_type_rent_upkeep.at[d.Building_Type, "upkeep"] * d.building_specs["Corridoor_size_per_floor"] * (1 + Reforms["Corridoor Upkeep"])
    return (elevator + stairwell + corridoor) * 12 * d.building_specs["Stories"]

def Amenity_Annual_Upkeep(selected_amenities, amenity_counts):
    # Annual upkeep for all selected amenities (from amenity_menu), multiplied by count
    amenity_selected = d.amenity_menu[d.amenity_menu["Amenity"].isin(selected_amenities)]
    return sum(
        row["Annual Upkeep"] * amenity_counts.get(row["Amenity"], 0)
        for _, row in amenity_selected.iterrows()
    )

def Amenity_Annual_Rent(selected_amenities, amenity_counts):
    # Annual rent from amenities whose rent is NOT already captured in the pro forma
    # through another mechanism (Ramen Shop rent flows through Retail_floors/Rentable_area_retail).
    # Currently this captures Subsidized Housing rent (60% of market).
    amenity_selected = d.amenity_menu[
        (d.amenity_menu["Amenity"].isin(selected_amenities)) &
        (d.amenity_menu["Amenity"] != "Ramen Shop")  # already handled via retail rent
    ]
    return sum(
        row["Annual Rent"] * amenity_counts.get(row["Amenity"], 0)
        for _, row in amenity_selected.iterrows()
    )

def Rent_Upkeep_Multiplier(rent_or_upkeep, space_type, area_key, reform_key):
    # Calculates annual rent or upkeep for a given space type
    # All data pulled live from d. so it always reflects proforma_inputs_updater changes
    # Vacancy rate and 12 months are baked in (they never vary per call)
    rate_per_sqft_month = d.building_type_rent_upkeep.at[space_type, rent_or_upkeep]
    area = d.building_specs[area_key]
    vacancy = d.misc_items["Vacancy Rate"]
    reform = Reforms[reform_key]
    return rate_per_sqft_month * area * 12 * (1 - vacancy) * (1 + reform)


#==========================================

#2/12/26 update: keep updating pro forma to include accurate calculations of amenities
def Period_0_ProForma(Table, total_FAR_Bonus, selected_amenities):
    Relevant_table = Table
    Relevant_table.at["Rent", 0] = 0

    # Hard Costs: building construction (ex land) + amenity construction costs
    # All values from d.Construction_Costs (negative = cost outflow)
    Relevant_table.at["Hard Costs", 0] = d.Construction_Costs["Total_ex_land"] + d.Construction_Costs["Amenities"]

    # Soft Costs: percentage of hard costs (from d.misc_items["Soft costs"])
    Relevant_table.at["Soft Costs", 0] = Relevant_table.at["Hard Costs", 0] * d.misc_items["Soft costs"]

    # Land Costs: land area * price per sqft of land
    Relevant_table.at["Land Costs", 0] = d.construction_costs_noncore["Land"] * d.input_factors["Land_plot_size"]

    Relevant_table.at["Upkeep", 0] = 0
    Relevant_table.at["Net Operating Income", 0] = 0
    Relevant_table.at["Other Expenses", 0] = 0
    Relevant_table.at["Debt Inflow/Outflow", 0] = abs(Relevant_table.at["Hard Costs", 0] * d.misc_items["Debt"])
    Relevant_table.at["Remaining Debt", 0] = Relevant_table.at["Hard Costs", 0] * d.misc_items["Debt"]
    Relevant_table.at["Property Sold Inflow", 0] = 0
    Relevant_table.at["Pre-Tax Cash Flow", 0] = Relevant_table.at["Hard Costs", 0] + Relevant_table.at["Soft Costs", 0] + Relevant_table.at["Land Costs", 0] + Relevant_table.at["Debt Inflow/Outflow", 0]

def Period_1_ProForma(selected_amenities, amenity_counts): #no delay
    # Rent: market-rate residential + retail + subsidized amenity rent
    # Rentable_area_residential now excludes subsidized space, so market-rate rent is correct.
    # Subsidized rent (e.g. 60% of market for affordable housing) comes from Amenity_Annual_Rent.
    residential_rent = Rent_Upkeep_Multiplier("rent", d.Building_Type, "Rentable_area_residential", "Rent Residential")
    retail_rent = Rent_Upkeep_Multiplier("rent", "Retail_floors", "Rentable_area_retail", "Rent Retail")
    amenity_rent = Amenity_Annual_Rent(selected_amenities, amenity_counts)
    ProForma_Table.at["Rent", 1] = residential_rent + retail_rent + amenity_rent

    # Upkeep: residential + retail + core/corridoor + amenity upkeep
    residential_upkeep = Rent_Upkeep_Multiplier("upkeep", d.Building_Type, "Rentable_area_residential", "Upkeep Residential")
    retail_upkeep = Rent_Upkeep_Multiplier("upkeep", "Retail_floors", "Rentable_area_retail", "Upkeep Retail")
    ProForma_Table.at["Upkeep", 1] = residential_upkeep + retail_upkeep + Core_and_Corridoor_Upkeep() + Amenity_Annual_Upkeep(selected_amenities, amenity_counts)

    ProForma_Table.at["Net Operating Income", 1] = ProForma_Table.at["Rent", 1] + ProForma_Table.at["Upkeep", 1]
    ProForma_Table.at["Other Expenses", 1] = ProForma_Table.at["Net Operating Income", 1] * d.misc_items["Other Expenses"]
    ProForma_Table.at["Debt Inflow/Outflow", 1] = -ProForma_Table.at["Debt Inflow/Outflow", 0] * d.misc_items["Mortgage Constant No Delay"]
    ProForma_Table.at["Remaining Debt", 1] = (ProForma_Table.at["Remaining Debt", 0] * (1 + d.misc_items["Debt Interest Rate"])) - ProForma_Table.at["Debt Inflow/Outflow", 1]
    ProForma_Table.at["Property Sold Inflow", 1] = 0
    ProForma_Table.at["Pre-Tax Cash Flow", 1] = ProForma_Table.at["Net Operating Income", 1] + ProForma_Table.at["Other Expenses", 1] + ProForma_Table.at["Debt Inflow/Outflow", 1]

    ProForma_Table.at["Hard Costs", 1] = 0
    ProForma_Table.at["Soft Costs", 1] = 0
    ProForma_Table.at["Land Costs", 1] = 0

def Period_2plus_ProForma(period, selected_amenities, amenity_counts): #no delay
    # Rent: previous period rent grown by rent increase rate
    ProForma_Table.at["Rent", period] = ProForma_Table.at["Rent", period-1] * (1 + d.misc_items["Rent Increase Rate"])

    # Upkeep: previous period upkeep grown by upkeep increase rate + core/corridoor + amenity upkeep
    ProForma_Table.at["Upkeep", period] = (ProForma_Table.at["Upkeep", period-1] * (1 + d.misc_items["Upkeep Increase Rate"])
        + Core_and_Corridoor_Upkeep() + Amenity_Annual_Upkeep(selected_amenities, amenity_counts))

    ProForma_Table.at["Net Operating Income", period] = ProForma_Table.at["Rent", period] + ProForma_Table.at["Upkeep", period]
    ProForma_Table.at["Other Expenses", period] = ProForma_Table.at["Net Operating Income", period] * d.misc_items["Other Expenses"]
    ProForma_Table.at["Debt Inflow/Outflow", period] = -ProForma_Table.at["Debt Inflow/Outflow", 0] * d.misc_items["Mortgage Constant No Delay"] if period <= d.misc_items["Periods"] else 0
    ProForma_Table.at["Remaining Debt", period] = (ProForma_Table.at["Remaining Debt", period-1] * (1 + d.misc_items["Debt Interest Rate"])) - ProForma_Table.at["Debt Inflow/Outflow", period]
    ProForma_Table.at["Property Sold Inflow", period] = 0
    ProForma_Table.at["Pre-Tax Cash Flow", period] = ProForma_Table.at["Net Operating Income", period] + ProForma_Table.at["Other Expenses", period] + ProForma_Table.at["Debt Inflow/Outflow", period]

    ProForma_Table.at["Hard Costs", period] = 0
    ProForma_Table.at["Soft Costs", period] = 0
    ProForma_Table.at["Land Costs", period] = 0


def run_proforma(total_FAR_Bonus, selected_amenities, amenity_counts):

    for period in range(d.misc_items["Periods"] + 2): #+2 because of zero indexing
        if period == 0:
            Period_0_ProForma(ProForma_Table, total_FAR_Bonus, selected_amenities)
        elif period == 1:
            Period_1_ProForma(selected_amenities, amenity_counts)
        else:
            Period_2plus_ProForma(period, selected_amenities, amenity_counts)

    ProForma_Table.at["Property Sold Inflow", d.misc_items["Periods"]] = Property_Sell_value(d.misc_items["Periods"])
    ProForma_Table.at["Pre-Tax Cash Flow", d.misc_items["Periods"]] += ProForma_Table.at["Property Sold Inflow", d.misc_items["Periods"]]

    return ProForma_Table

def profit_calculator(proforma_table_forprofit):
    
    # Extract Pre-Tax Cash Flow row as a list of values
    cash_flows = proforma_table_forprofit.loc["Pre-Tax Cash Flow"].values
    
    # Calculate IRR using numpy_financial
    # IRR is the discount rate that makes NPV = 0
    irr = nf.irr(cash_flows)
    
    # Calculate NPV using the discount rate from misc_items
    discount_rate = d.misc_items["Discount Rate"]
    npv = nf.npv(discount_rate, cash_flows)
    
    return irr, npv


def second_developer_cycle():
    st.write("Now we play as a second developer. The amenities you already chose will depreciate in value, to make different amenities more appealing.")
    st.write("Here are the current count of your amenities, and their FAR bonuses on the margin:")
    
    # Get current committed amenity counts
    amenity_counts = st.session_state.get("amenity_counts_committed", {
        row["Amenity"]: 0 for _, row in d.amenity_menu.iterrows()
    })
    
    rows = []
    for _, row in d.amenity_menu.iterrows():
        name = row["Amenity"]
        per_unit_bonus = row["FAR Bonus"]
        current_count = amenity_counts.get(name, 0)
        
        # Calculate current scaled bonus
        if current_count <= 0:
            scaled_count_current = 0
        elif current_count <= 1:
            scaled_count_current = current_count
        else:
            scaled_count_current = np.log(current_count) + 1
        
        # Calculate scaled bonus if we add one more
        next_count = current_count + 1
        if next_count <= 1:
            scaled_count_next = next_count
        else:
            scaled_count_next = np.log(next_count) + 1
        
        # Marginal bonus = incremental difference
        marginal_bonus = (scaled_count_next - scaled_count_current) * per_unit_bonus
        
        rows.append({
            "Amenity": name,
            "Current Count": current_count,
            "Marginal FAR Bonus (+1)": round(marginal_bonus, 4)
        })
    
    marginal_df = pd.DataFrame(rows)
    st.write(marginal_df)


def game_summary():
    """Page 8: display a summary of both rounds — amenities, FAR bonuses, NPV and IRR."""
    st.title("Game Summary")

    # ── helpers ──────────────────────────────────────────────────────────────
    def _fmt_pct(val):
        try:
            return f"{val * 100:.2f}%"
        except (TypeError, ValueError):
            return "N/A"

    def _fmt_dollar(val):
        try:
            return f"${val:,.0f}"
        except (TypeError, ValueError):
            return "N/A"

    def _amenity_table(counts_dict):
        """Return a DataFrame showing only amenities with count > 0."""
        rows = [
            {"Amenity": name, "Count": count}
            for name, count in counts_dict.items()
            if count > 0
        ]
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Amenity", "Count"])

    # ── retrieve saved data ───────────────────────────────────────────────────
    far_r1 = st.session_state.get("total_FAR_Bonus_round1", None)
    far_r2 = st.session_state.get("total_FAR_Bonus_round2", None)
    irr_r1 = st.session_state.get("irr_round1", None)
    npv_r1 = st.session_state.get("npv_round1", None)
    irr_r2 = st.session_state.get("irr_round2", None)
    npv_r2 = st.session_state.get("npv_round2", None)
    counts_r1 = st.session_state.get("amenity_counts_round1", {})
    counts_r2_delta = st.session_state.get("amenity_counts_round2_delta", {})

    col1, col2 = st.columns(2)

    # ── Round 1 ───────────────────────────────────────────────────────────────
    with col1:
        st.subheader("Round 1")

        st.markdown("**Amenities selected**")
        tbl1 = _amenity_table(counts_r1)
        if not tbl1.empty:
            st.dataframe(tbl1, use_container_width=True, hide_index=True)
        else:
            st.write("No amenities selected.")

        st.metric("Total FAR Bonus", round(far_r1, 2) if far_r1 is not None else "N/A")
        st.metric("IRR", _fmt_pct(irr_r1))
        st.metric("NPV", _fmt_dollar(npv_r1))

    # ── Round 2 ───────────────────────────────────────────────────────────────
    with col2:
        st.subheader("Round 2")

        st.markdown("**New amenities added this round**")
        tbl2 = _amenity_table(counts_r2_delta)
        if not tbl2.empty:
            st.dataframe(tbl2, use_container_width=True, hide_index=True)
        else:
            st.write("No new amenities added.")

        st.metric("Round FAR Bonus", round(far_r2, 2) if far_r2 is not None else "N/A")
        st.metric("IRR", _fmt_pct(irr_r2))
        st.metric("NPV", _fmt_dollar(npv_r2))