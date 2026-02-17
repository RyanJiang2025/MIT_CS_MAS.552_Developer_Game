import pandas as pd
import numpy as np

#NOTE: redo all numbers for the city of Boston

Input_factors = { #Item sizing
    "Apt_size" : 700,
    "Land_plot_size" : 10000,
    "Stairwell_size" : 90,
    "Elevator_size" : 60,
}

Building_Specifications = { #design of the floor and of the building
    "Stories" : 0,
    "Apt_number_per_floor" : 0,
    "Elevator_per_floor" : 0,
    "Stairwell_per_floor" : 0,
    "Corridoor_size_per_floor" : 0,
    "Non-Buildable_Area" : 0,
    "Retail_floors" : 0,
}



Building_Type_maxheight = { #this is the max height of each building type. This matters for the construction costs. So if a building is <= lowrise height, it will use the lowrise construction costs, etc.
    "Lowrise" : 4,
    "Midrise_short" : 10,
    "Midrise_tall" : 16,
    "Highrise" : 1000,
}

Construction_costs_noncore = { #construction costs per square foot for non-core items
    "Land" : -1000,
    "Lowrise" : -550,
    "Midrise_short" : -650,
    "Midrise_tall" : -750,
    "Highrise" : -900,
}

Construction_costs_core = { #construction costs per item for core items
    "Elevator" : -375000,
    "Stairwell" : -150000,
}

#Determine rent and upkeep for each building type
Building_Type_rent_upkeep = pd.DataFrame(
    index=[
        "Lowrise",
        "Midrise_short",
        "Midrise_tall",
        "Highrise",
        "Retail_floors", #Retail within this context means ramen shop
        "Elevator",
        "Stairwell",
    ],
    data={
        "rent": [4.5, 5.5, 5.5, 7.0, 6.0, 0, 0], #monthly per square foot
        "upkeep": [-0.5, -0.5, -0.5, -0.5, -1.5, -8000/12, -2000/12], #monthly per square foot
    },
)

#Add reforms in later, they likely interact directly with the pro forma table
#Same with Architectural Robotics, this can be an add on later

Miscellaneous_Items = {
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
    "Periods" : 9 #Length of the pro forma in years
}

Mortgage_Constant_No_Delay = Miscellaneous_Items["Debt Interest Rate"]/(1-(1+Miscellaneous_Items["Debt Interest Rate"])**(-1*Miscellaneous_Items["Periods"]))
Mortgage_Constant_With_Delay = Miscellaneous_Items["Debt Interest Rate"]/(1-(1+Miscellaneous_Items["Debt Interest Rate"])**(-1*(Miscellaneous_Items["Periods"]-Miscellaneous_Items["Years of Delay"])))
Miscellaneous_Items["Mortgage Constant No Delay"] = Mortgage_Constant_No_Delay
Miscellaneous_Items["Mortgage Constant With Delay"] = Mortgage_Constant_With_Delay

#==========================================
#Updates the Building_Specifications with the Buildable_Area, Rentable_area_residential, and Rentable_area_retail so we can contain them all in one dictionary
Buildable_Area = Input_factors["Land_plot_size"] - Building_Specifications["Non-Buildable_Area"]
Rentable_area_residential = Building_Specifications["Apt_number_per_floor"] * (Building_Specifications["Stories"]-Building_Specifications['Retail_floors']) * Input_factors["Apt_size"]
Rentable_area_retail = Buildable_Area * Building_Specifications["Retail_floors"]
Building_Specifications["Buildable_Area"] = Buildable_Area
Building_Specifications["Rentable_area_residential"] = Rentable_area_residential
Building_Specifications["Rentable_area_retail"] = Rentable_area_retail


#==========================================
#Error checks
if not Building_Type_maxheight["Lowrise"] < Building_Type_maxheight["Midrise_short"] < Building_Type_maxheight["Midrise_tall"] < Building_Type_maxheight["Highrise"]:
    print("ERROR: Building type heights are not in order. Please check the Building_Type_maxheight dictionary.")
    exit()

if Building_Specifications["Apt_number_per_floor"]*Input_factors["Apt_size"]+Building_Specifications["Elevator_per_floor"]*Input_factors["Elevator_size"]+Building_Specifications["Stairwell_per_floor"]*Input_factors["Stairwell_size"]+Building_Specifications["Corridoor_size_per_floor"] > (Input_factors["Land_plot_size"] - Building_Specifications["Non-Buildable_Area"]):
    print("ERROR: The total size of the apartments, elevators, corridoors and stairwells is greater than the per-floor buildable area. Please check the Input_factors and Building_Specifications dictionaries.")
    exit()
    
if Miscellaneous_Items["Years of Delay"] >= Miscellaneous_Items["Periods"]:
    print("ERROR: Years of delay must be less than the periods (time length of the pro forma). Please check the Miscellaneous_Items dictionary.")
    exit()

if Miscellaneous_Items["Years of Delay"] < 0 or Miscellaneous_Items["Years of Delay"] > Miscellaneous_Items["Periods"]:
    print("ERROR: Years of delay must be between 0 and the periods (time length of the pro forma). Please check the Miscellaneous_Items dictionary.")
    exit()

#Other errors that could go wrong (e.g. land size < apartment size), but add in stupid error messages later.

#==========================================

#Determine the building type
if Building_Specifications["Stories"] <= Building_Type_maxheight["Lowrise"]:
    Building_Type = "Lowrise"
elif Building_Specifications["Stories"] <= Building_Type_maxheight["Midrise_short"]:
    Building_Type = "Midrise_short"
elif Building_Specifications["Stories"] <= Building_Type_maxheight["Midrise_tall"]:
    Building_Type = "Midrise_tall"
else:
    Building_Type = "Highrise"

#Determine the construction costs
Construction_Costs = {
    "Land" : Construction_costs_noncore["Land"]*Input_factors["Land_plot_size"],
    "Residential" : Construction_costs_noncore[Building_Type]*Building_Specifications["Rentable_area_residential"],
    "Retail" : Construction_costs_noncore[Building_Type]*Building_Specifications["Rentable_area_retail"],
    "Corridoor" : Construction_costs_noncore[Building_Type]*Building_Specifications["Corridoor_size_per_floor"]*Building_Specifications["Stories"],
    "Elevator" : Construction_costs_core["Elevator"]*Building_Specifications["Elevator_per_floor"]*Building_Specifications["Stories"],
    "Stairwell" : Construction_costs_core["Stairwell"]*Building_Specifications["Stairwell_per_floor"]*Building_Specifications["Stories"],
    "Total" : Construction_costs_noncore["Land"]*Input_factors["Land_plot_size"] + Construction_costs_noncore[Building_Type]*Building_Specifications["Rentable_area_residential"] + Construction_costs_noncore[Building_Type]*Building_Specifications["Rentable_area_retail"] + Construction_costs_noncore[Building_Type]*Building_Specifications["Corridoor_size_per_floor"]*Building_Specifications["Stories"] + Construction_costs_core["Elevator"]*Building_Specifications["Elevator_per_floor"]*Building_Specifications["Stories"] + Construction_costs_core["Stairwell"]*Building_Specifications["Stairwell_per_floor"]*Building_Specifications["Stories"],
    "Total_ex_land" : Construction_costs_noncore[Building_Type]*Building_Specifications["Rentable_area_residential"] + Construction_costs_noncore[Building_Type]*Building_Specifications["Rentable_area_retail"] + Construction_costs_noncore[Building_Type]*Building_Specifications["Corridoor_size_per_floor"]*Building_Specifications["Stories"] + Construction_costs_core["Elevator"]*Building_Specifications["Elevator_per_floor"]*Building_Specifications["Stories"] + Construction_costs_core["Stairwell"]*Building_Specifications["Stairwell_per_floor"]*Building_Specifications["Stories"]
}

