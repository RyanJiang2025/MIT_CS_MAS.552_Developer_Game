from proforma_inputs import Miscellaneous_Items as MiscItems

#NOTE: many of these are percentages, so 0.5 will bne interpreted as 50%. They are also sign-sensitive, so +0.5 will be interpreted as +50% and -0.5 will be interpreted as -50%.

Reform_effects = {
    "Rent Residential": +0.0, #write as percentage
    "Upkeep Residential": -0.0, #write as percentage
    "Rent Retail": +0.0, #write as percentage
    "Upkeep Retail": -0.0, #write as percentage
    "Hard Costs": -0.0, #write as percentage
    "Soft Costs": -0.0, #write as percentage
    "Land Costs": -0.0, #write as percentage
    "Delays Changes": 0, #years
    "Corridoor Upkeep": -0.0, #write as percentage
    "Stairwell Upkeep": -0.0, #write as percentage
    "Elevator Upkeep": -0.0, #write as percentage
}

def reform_checks():
    if 1 + Reform_effects["Rent Residential"] <= 0:
        print("ERROR: Residential rent cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Upkeep Residential"] <= 0:
        print("ERROR: Residential upkeep cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Rent Retail"] <= 0:
        print("ERROR: Retail rent cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Upkeep Retail"] <= 0:
        print("ERROR: Retail upkeep cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Hard Costs"] <= 0:
        print("ERROR: Hard costs cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Soft Costs"] <= 0:
        print("ERROR: Soft costs cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Land Costs"] <= 0:
        print("ERROR: Land costs cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Corridoor Upkeep"] <= 0:
        print("ERROR: Corridoor upkeep cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Stairwell Upkeep"] <= 0:
        print("ERROR: Stairwell upkeep cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 1 + Reform_effects["Elevator Upkeep"] <= 0:
        print("ERROR: Elevator upkeep cannot be zero or below. Please check the Reform_effects dictionary.")
        exit()
    if 0 > MiscItems["Years of Delay"] + Reform_effects["Delays Changes"] or MiscItems["Years of Delay"] + Reform_effects["Delays Changes"] > MiscItems["Periods"]:
        print("ERROR: Delays changes are not within the valid range. Please check the Reform_effects dictionary.")
        exit()

reform_checks()