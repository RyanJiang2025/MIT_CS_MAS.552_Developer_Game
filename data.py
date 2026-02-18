from decimal import ROUND_DOWN
import pandas as pd
from math import floor

from proforma_reforms import MiscItems

FAR_Booster = 2 # * 1.5

input_factors = { #Item sizing
    "Apt_size" : 700,
    "Land_plot_size" : 10000,
    "Stairwell_size" : 90,
    "Elevator_size" : 60,
}

building_specs = { #design of the floor and of the building
    "Stories" : 6,
    "Elevator_per_floor" : 0,
    "Stairwell_per_floor" : 0,
    "Corridoor_size_per_floor" : 0,
    "Non-Buildable_Area" : 0,
    "Retail_floors" : 0,
    "Subsidized_floors" : 0,
}
building_specs["Residential_floors"] = building_specs["Stories"] - building_specs['Retail_floors']

building_type_maxheight = { #this is the max height of each building type. This matters for the construction costs. So if a building is <= lowrise height, it will use the lowrise construction costs, etc.
    "Lowrise" : 4,
    "Midrise_short" : 10,
    "Midrise_tall" : 16,
    "Highrise" : 1000,
}

construction_costs_noncore = { #construction costs per square foot for non-core items
    "Land" : -1000,
    "Lowrise" : -550,
    "Midrise_short" : -650,
    "Midrise_tall" : -750,
    "Highrise" : -900,
}

construction_costs_core = { #construction costs per item for core items
    "Elevator" : -375000,
    "Stairwell" : -150000
}

building_type_rent_upkeep = pd.DataFrame(
    index=[
        "Lowrise",
        "Midrise_short",
        "Midrise_tall",
        "Highrise",
        "Retail_floors", #Retail within this context means ramen shop
        "Elevator",
        "Stairwell"
    ],
    data={
        "rent": [4.5, 5.5, 5.5, 7.0, 6.0, 0, 0], #monthly per square foot
        "upkeep": [-0.5, -0.5, -0.5, -0.5, -1.5, -8000/12, -2000/12] #monthly per square foot
    },
)

misc_items = {
    "Soft costs" : 0.22, #calculated as a percentage of hard costs
    "Debt" : 0.6, #calculated as a percentage of hard costs
    "Debt Interest Rate" : 0.10,
    "Vacancy Rate" : 0.10,
    "Rent Increase Rate" : 0.10,
    "Upkeep Increase Rate" : 0.04,
    "Other Expenses" : -0.10,
    "Discount Rate" : 0.08,
    "Exit Value Multiple" : 10,
    "Years of Delay" : 3,
    "Periods" : 9, #Length of the pro forma in years
    "Affordable_Apt_Subsidy" : 0.4
}

Mortgage_Constant_No_Delay = misc_items["Debt Interest Rate"]/(1-(1+misc_items["Debt Interest Rate"])**(-1*misc_items["Periods"]))
Mortgage_Constant_With_Delay = misc_items["Debt Interest Rate"]/(1-(1+misc_items["Debt Interest Rate"])**(-1*(misc_items["Periods"]-misc_items["Years of Delay"])))
misc_items["Mortgage Constant No Delay"] = Mortgage_Constant_No_Delay
misc_items["Mortgage Constant With Delay"] = Mortgage_Constant_With_Delay

#Updates the Building_Specifications with the Buildable_Area, Rentable_area_residential, and Rentable_area_retail so we can contain them all in one dictionary
#However, these are all endogenous, so these need to be updated in functions.py after initial amenity selection.
Buildable_Area = input_factors["Land_plot_size"] - building_specs["Non-Buildable_Area"]
Rentable_area_residential =  Buildable_Area * building_specs["Residential_floors"]
Rentable_area_retail = Buildable_Area * building_specs["Retail_floors"]
Rentable_area_subsidized = Buildable_Area * building_specs["Subsidized_floors"]
building_specs["Buildable_Area"] = Buildable_Area
building_specs["Rentable_area_residential"] = Rentable_area_residential
building_specs["Rentable_area_retail"] = Rentable_area_retail
building_specs["Rentable_area_subsidized"] = Rentable_area_subsidized

#Determine the building type
#We run this initially with the pre-FAR_bonus height, and then update in functions.py after FAR bonus is selected.
if building_specs["Stories"] <= building_type_maxheight["Lowrise"]:
    Building_Type = "Lowrise"
elif building_specs["Stories"] <= building_type_maxheight["Midrise_short"]:
    Building_Type = "Midrise_short"
elif building_specs["Stories"] <= building_type_maxheight["Midrise_tall"]:
    Building_Type = "Midrise_tall"
else:
    Building_Type = "Highrise"

#Determine the construction costs
#Also needs to be updated in functions.py after initial amenity selection, with building_type, rentable_area_residential, rentable_area_retail, stories, and the amenities we added.
#Also, how exactly do we calculate amenity costs in the pro forma?
Construction_Costs = {
    "Land" : construction_costs_noncore["Land"]*input_factors["Land_plot_size"],
    "Residential" : construction_costs_noncore[Building_Type]*building_specs["Rentable_area_residential"],
    "Retail" : construction_costs_noncore[Building_Type]*building_specs["Rentable_area_retail"],
    "Corridoor" : construction_costs_noncore[Building_Type]*building_specs["Corridoor_size_per_floor"]*building_specs["Stories"],
    "Elevator" : construction_costs_core["Elevator"]*building_specs["Elevator_per_floor"]*building_specs["Stories"],
    "Stairwell" : construction_costs_core["Stairwell"]*building_specs["Stairwell_per_floor"]*building_specs["Stories"],
    "Total" : construction_costs_noncore["Land"]*input_factors["Land_plot_size"] + construction_costs_noncore[Building_Type]*building_specs["Rentable_area_residential"] + construction_costs_noncore[Building_Type]*building_specs["Rentable_area_retail"] + construction_costs_noncore[Building_Type]*building_specs["Corridoor_size_per_floor"]*building_specs["Stories"] + construction_costs_core["Elevator"]*building_specs["Elevator_per_floor"]*building_specs["Stories"] + construction_costs_core["Stairwell"]*building_specs["Stairwell_per_floor"]*building_specs["Stories"],
    "Total_ex_land" : construction_costs_noncore[Building_Type]*building_specs["Rentable_area_residential"] + construction_costs_noncore[Building_Type]*building_specs["Rentable_area_retail"] + construction_costs_noncore[Building_Type]*building_specs["Corridoor_size_per_floor"]*building_specs["Stories"] + construction_costs_core["Elevator"]*building_specs["Elevator_per_floor"]*building_specs["Stories"] + construction_costs_core["Stairwell"]*building_specs["Stairwell_per_floor"]*building_specs["Stories"]
}

#==========================================

#define variables that are used in data.py
#We may also need to update these too IF we use them in functions.py for the pro forma. However, if they are only used in amenuty_menu then this may be ok, and in fact preferable so that increasing the height limit over a breakpoint (building_type) doesn't suddenly increase affordable housing costs.
Apt_size = input_factors["Apt_size"]
Apt_cost = Apt_size * construction_costs_noncore[Building_Type]
Apt_rent_annual = Apt_size * building_type_rent_upkeep.at[Building_Type, "rent"] * 12
Apt_upkeep_annual = Apt_size * building_type_rent_upkeep.at[Building_Type, "upkeep"] * 12

#defining height limits for activity
max_bonus_FAR = 3 #Maximum FAR bonus that can be added to the building height
maxheight_pre_bonus = building_specs["Stories"] #Maximum height of the building before the bonus is added
maxheight_post_bonus =  maxheight_pre_bonus + max_bonus_FAR

# Store original/base values that should never be mutated.
# FAR_bonus() uses these so its output stays stable across reruns
# even after proforma_inputs_updater mutates building_specs/Building_Type.
Base_Building_Type = Building_Type
Base_Buildable_Area = Buildable_Area

#results from the PV exercise
pv_results = pd.DataFrame({
    "Amenity": ["Pocket Park", "Ramen Shop", "City Science Lab", "Subsidized Housing", "Annual Festival", "Flood Mitigation"],
    "Votes": [1.607717, 2.146182, 1.542971, 1.750715, 1.512509, 1.439906]
})
# Normalize so lowest vote = 1, others scaled proportionally
pv_results["Votes"] = pv_results["Votes"] / pv_results["Votes"].min()



#amenity menu items
amenity_menu = pd.DataFrame({
    "Amenity": ["Pocket Park", "Ramen Shop", "City Science Lab", "Subsidized Housing", "Annual Festival", "Flood Mitigation"],
    "Cost": [-200000, -500000, -600000, Apt_cost, 0, -3000000],
    "Land Use": ["Setback", "On-Site", "Off-Site", "On-Site", "Off-Site", "Off-Site"],
    "Square Footage": [2000, 1500, 0, 700, Apt_size, 0],  # all off-site buildings are 0, all setback or in-building buildings are 100 as placeholders
    "Annual Rent": [0, 75000, 0, Apt_rent_annual*(1-misc_items["Affordable_Apt_Subsidy"]), 0, 0],
    "Annual Upkeep": [-10000, -15000, -100000, Apt_upkeep_annual, -30000, 0],
    "FAR Bonus": [0, 0, 0, 0, 0, 0],
})