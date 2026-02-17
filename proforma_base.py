from math import nan
import pandas as pd
import numpy as np
import numpy_financial as nf

from data import input_factors, building_specifications as buildspecs, construction_costs_noncore, construction_costs_core, rent_upkeep, building_type_maxheight, misc_items, mortgage_constant_no_delay, mortgage_constant_with_delay, building_type, construction_costs
from proforma_reforms import Reform_effects as Reforms

miscellaneous_items["Years of Delay"] += Reforms["Delays Changes"]

#NOTE: need to redo the calculations for the floors of mixed use.


ProForma_Table = pd.DataFrame(
    index=["Rent", "Hard Costs", "Soft Costs", "Land Costs", "Upkeep", "Net Operating Income", "Other Expenses", "Debt Inflow/Outflow", "Remaining Debt", "Property Sold Inflow", "Pre-Tax Cash Flow"],
    columns=range(misc_items["Periods"]+2)
)

def Property_Sell_value(final_period):
    return ProForma_Table.at["Net Operating Income", final_period + 1] * misc_items["Exit Value Multiple"]

def Core_and_Corridoor_Upkeep(): #Core and corridoor costs are already included in construction costs
    return (rent_upkeep.at["Elevator", "upkeep"] * buildspecs["Elevator_per_floor"] * (1 + Reforms["Elevator Upkeep"]) + rent_upkeep.at["Stairwell", "upkeep"] * buildspecs["Stairwell_per_floor"] * (1 + Reforms["Stairwell Upkeep"]) + rent_upkeep.at[building_type, "upkeep"] * buildspecs["Corridoor_size_per_floor"] * (1 + Reforms["Corridoor Upkeep"])) * 12 * buildspecs["Stories"]
#NOTE Need to still add this into the pro forma table without breaking everything.

def Rent_Upkeep_Multiplier(Rent_or_Upkeep, Type, Area, Vacancy, Months, reform_effect):
    return (rent_upkeep.at[Type, Rent_or_Upkeep] * buildspecs[Area]) * Months * (1 - Vacancy) * (1 + reform_effect)


#==========================================

def Period_0_ProForma(Table):
    Relevant_table = Table
    Relevant_table.at["Rent", 0] = 0
    Relevant_table.at["Hard Costs", 0] = construction_costs["Total_ex_land"] * (1 + Reforms["Hard Costs"])
    Relevant_table.at["Soft Costs", 0] = Relevant_table.at["Hard Costs", 0] * misc_items["Soft costs"] * (1 + Reforms["Soft Costs"])
    Relevant_table.at["Land Costs", 0] = construction_costs["Land"] * (1 + Reforms["Land Costs"])
    Relevant_table.at["Upkeep", 0] = 0
    Relevant_table.at["Net Operating Income", 0] = 0
    Relevant_table.at["Other Expenses", 0] = 0
    Relevant_table.at["Debt Inflow/Outflow", 0] = abs(Relevant_table.at["Hard Costs", 0] * misc_items["Debt"])
    Relevant_table.at["Remaining Debt", 0] = Relevant_table.at["Hard Costs", 0] * misc_items["Debt"]
    Relevant_table.at["Property Sold Inflow", 0] = 0
    Relevant_table.at["Pre-Tax Cash Flow", 0] = Relevant_table.at["Hard Costs", 0] + Relevant_table.at["Soft Costs", 0] + Relevant_table.at["Land Costs", 0] + Relevant_table.at["Debt Inflow/Outflow", 0]

def Period_1_ProForma(): #no delay
    ProForma_Table.at["Rent", 1] = Rent_Upkeep_Multiplier("rent", building_type, "Rentable_area_residential", misc_items["Vacancy Rate"], 12, Reforms["Rent Residential"]) + Rent_Upkeep_Multiplier("rent", "Retail_floors", "Rentable_area_retail", misc_items["Vacancy Rate"], 12, Reforms["Rent Retail"])
    ProForma_Table.at["Upkeep", 1] = Rent_Upkeep_Multiplier("upkeep", building_type, "Rentable_area_residential", misc_items["Vacancy Rate"], 12, Reforms["Upkeep Residential"]) + Rent_Upkeep_Multiplier("upkeep", "Retail_floors", "Rentable_area_retail", misc_items["Vacancy Rate"], 12, Reforms["Upkeep Retail"]) + Core_and_Corridoor_Upkeep()
    ProForma_Table.at["Net Operating Income", 1] = ProForma_Table.at["Rent", 1] + ProForma_Table.at["Upkeep", 1]
    ProForma_Table.at["Other Expenses", 1] = ProForma_Table.at["Net Operating Income", 1] * misc_items["Other Expenses"]
    ProForma_Table.at["Debt Inflow/Outflow", 1] = -ProForma_Table.at["Debt Inflow/Outflow", 0] * misc_items["Mortgage Constant No Delay"]
    ProForma_Table.at["Remaining Debt", 1] = (ProForma_Table.at["Remaining Debt", 0] * (1 + misc_items["Debt Interest Rate"])) - ProForma_Table.at["Debt Inflow/Outflow", 1]   
    ProForma_Table.at["Property Sold Inflow", 1] = 0
    ProForma_Table.at["Pre-Tax Cash Flow", 1] = ProForma_Table.at["Net Operating Income", 1] + ProForma_Table.at["Other Expenses", 1] + ProForma_Table.at["Debt Inflow/Outflow", 1]
    
    ProForma_Table.at["Hard Costs", 1] = 0
    ProForma_Table.at["Soft Costs", 1] = 0
    ProForma_Table.at["Land Costs", 1] = 0

def Period_2plus_ProForma(period): #no delay
    ProForma_Table.at["Rent", period] = ProForma_Table.at["Rent", period-1] * (1 + misc_items["Rent Increase Rate"])
    ProForma_Table.at["Upkeep", period] = ProForma_Table.at["Upkeep", period-1] * (1 + misc_items["Upkeep Increase Rate"]) + Core_and_Corridoor_Upkeep()
    ProForma_Table.at["Net Operating Income", period] = ProForma_Table.at["Rent", period] + ProForma_Table.at["Upkeep", period]
    ProForma_Table.at["Other Expenses", period] = ProForma_Table.at["Net Operating Income", period] * misc_items["Other Expenses"]
    ProForma_Table.at["Debt Inflow/Outflow", period] = -ProForma_Table.at["Debt Inflow/Outflow", 0] * misc_items["Mortgage Constant No Delay"] if period <= misc_items["Periods"] else 0
    ProForma_Table.at["Remaining Debt", period] = (ProForma_Table.at["Remaining Debt", period-1] * (1 + misc_items["Debt Interest Rate"])) - ProForma_Table.at["Debt Inflow/Outflow", period]
    ProForma_Table.at["Property Sold Inflow", period] = 0
    ProForma_Table.at["Pre-Tax Cash Flow", period] = ProForma_Table.at["Net Operating Income", period] + ProForma_Table.at["Other Expenses", period] + ProForma_Table.at["Debt Inflow/Outflow", period]

    ProForma_Table.at["Hard Costs", period] = 0
    ProForma_Table.at["Soft Costs", period] = 0
    ProForma_Table.at["Land Costs", period] = 0

for period in range(misc_items["Periods"] + 2): #+2 because of zero indexing
    if period == 0:
        Period_0_ProForma(ProForma_Table)
    elif period == 1:
        Period_1_ProForma()
    else:
        Period_2plus_ProForma(period)

ProForma_Table.at["Property Sold Inflow", misc_items["Periods"]] = Property_Sell_value(misc_items["Periods"])
ProForma_Table.at["Pre-Tax Cash Flow", misc_items["Periods"]] += ProForma_Table.at["Property Sold Inflow", misc_items["Periods"]]

ProForma_Table_Delay = pd.DataFrame(
    index=["Rent", "Hard Costs", "Soft Costs", "Land Costs", "Upkeep", "Net Operating Income", "Other Expenses", "Debt Inflow/Outflow", "Remaining Debt", "Property Sold Inflow", "Pre-Tax Cash Flow"],
    columns=range(misc_items["Periods"]+2)
)

def Period_1_ProForma_Delay(): #no delay
    ProForma_Table_Delay.at["Rent", 1] = ProForma_Table.at["Rent", 1] if period > misc_items["Years of Delay"] else 0   
    ProForma_Table_Delay.at["Upkeep", 1] = ProForma_Table.at["Upkeep", 1] if period > misc_items["Years of Delay"] else 0
    ProForma_Table_Delay.at["Net Operating Income", 1] = ProForma_Table_Delay.at["Rent", 1] + ProForma_Table_Delay.at["Upkeep", 1]
    ProForma_Table_Delay.at["Other Expenses", 1] = ProForma_Table.at["Other Expenses", 1]
    ProForma_Table_Delay.at["Debt Inflow/Outflow", 1] = -ProForma_Table_Delay.at["Debt Inflow/Outflow", 0] * misc_items["Mortgage Constant With Delay"] if period > misc_items["Years of Delay"] else 0
    ProForma_Table_Delay.at["Remaining Debt", 1] = (ProForma_Table_Delay.at["Remaining Debt", 0] * (1 + misc_items["Debt Interest Rate"])) - ProForma_Table_Delay.at["Debt Inflow/Outflow", 1]   
    ProForma_Table_Delay.at["Property Sold Inflow", 1] = 0
    ProForma_Table_Delay.at["Pre-Tax Cash Flow", 1] = ProForma_Table_Delay.at["Net Operating Income", 1] + ProForma_Table_Delay.at["Other Expenses", 1] + ProForma_Table_Delay.at["Debt Inflow/Outflow", 1]
    
    ProForma_Table_Delay.at["Hard Costs", 1] = 0
    ProForma_Table_Delay.at["Soft Costs", 1] = 0
    ProForma_Table_Delay.at["Land Costs", 1] = 0

def Period_2plus_ProForma_Delay(period): #no delay
    ProForma_Table_Delay.at["Rent", period] = ProForma_Table.at["Rent", period] if period > misc_items["Years of Delay"] else 0
    ProForma_Table_Delay.at["Upkeep", period] = ProForma_Table.at["Upkeep", period] if period > misc_items["Years of Delay"] else 0
    ProForma_Table_Delay.at["Net Operating Income", period] = ProForma_Table_Delay.at["Rent", period] + ProForma_Table_Delay.at["Upkeep", period]
    ProForma_Table_Delay.at["Other Expenses", period] = ProForma_Table_Delay.at["Net Operating Income", period] * misc_items["Other Expenses"]
    ProForma_Table_Delay.at["Debt Inflow/Outflow", period] = -ProForma_Table_Delay.at["Debt Inflow/Outflow", 0] * misc_items["Mortgage Constant With Delay"] if period <= misc_items["Periods"] else 0
    ProForma_Table_Delay.at["Remaining Debt", period] = (ProForma_Table_Delay.at["Remaining Debt", period-1] * (1 + misc_items["Debt Interest Rate"])) - ProForma_Table_Delay.at["Debt Inflow/Outflow", period]
    ProForma_Table_Delay.at["Property Sold Inflow", period] = 0
    ProForma_Table_Delay.at["Pre-Tax Cash Flow", period] = ProForma_Table_Delay.at["Net Operating Income", period] + ProForma_Table_Delay.at["Other Expenses", period] + ProForma_Table_Delay.at["Debt Inflow/Outflow", period]

    ProForma_Table_Delay.at["Hard Costs", period] = 0
    ProForma_Table_Delay.at["Soft Costs", period] = 0
    ProForma_Table_Delay.at["Land Costs", period] = 0

for period in range(misc_items["Periods"] + 2): #+2 because of zero indexing
    if period == 0:
        Period_0_ProForma(ProForma_Table_Delay)
    elif period == 1:
        Period_1_ProForma_Delay()
    else:
        Period_2plus_ProForma_Delay(period)

ProForma_Table_Delay.at["Property Sold Inflow", misc_items["Periods"]] = Property_Sell_value(misc_items["Periods"])
ProForma_Table_Delay.at["Pre-Tax Cash Flow", misc_items["Periods"]] += ProForma_Table_Delay.at["Property Sold Inflow", misc_items["Periods"]]

#==========================================

print("==================== ProForma Calculator ====================")
print("--------------------------------")
print("Input Factors")
print(input_factors)
print("--------------------------------")
print("Building Specifications")
print(buildspecs)
print("--------------------------------")
print("Construction Costs")
print(construction_costs)
print("--------------------------------")
print("Rent and Upkeep")
print(rent_upkeep)
print("--------------------------------")
print("Core and Corridoor Upkeep")
print(Core_and_Corridoor_Upkeep())
print("--------------------------------")
print("Miscellaneous Items")
print(misc_items)
print("--------------------------------")

#==========================================
#Note that because some items are calculated assuming no delay even in the delay table (for example other expenses as a percentage of NOI), the delay table only functions when we calculate the no delay table first.
print("ProForma Table :", misc_items["Periods"], "periods")
print(ProForma_Table.loc[:, :misc_items["Periods"]])

print()
print("IRR: ", round(nf.irr(ProForma_Table.loc["Pre-Tax Cash Flow", :misc_items["Periods"]].values) * 100, 2), "%")
print("NPV: ", "$" + str(round(nf.npv(misc_items["Discount Rate"], ProForma_Table.loc["Pre-Tax Cash Flow", :misc_items["Periods"]].values), 2)))

print("--------------------------------")

if misc_items["Years of Delay"] > 0:
    print("ProForma Table with Delay :", misc_items["Years of Delay"], "years of delay,", misc_items["Periods"], "periods")
    print(ProForma_Table_Delay.loc[:, :misc_items["Periods"]])

print()
print("IRR: ", round(nf.irr(ProForma_Table_Delay.loc["Pre-Tax Cash Flow", :misc_items["Periods"]].values) * 100, 2), "%")
print("NPV: ", "$" + str(round(nf.npv(misc_items["Discount Rate"], ProForma_Table_Delay.loc["Pre-Tax Cash Flow", :misc_items["Periods"]].values), 2)))
print("--------------------------------")