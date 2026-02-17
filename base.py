import functions as f
import data as d
import streamlit as st

st.session_state.setdefault("page", 1)

st.set_page_config(page_title="Week 3 Developer Game", page_icon=":building_construction:", layout="wide")

# Compute FAR bonuses once on every rerun so d.amenity_menu is always up to date
d.amenity_menu = f.FAR_bonus_menu()

if st.session_state.page == 1:
    
    # Reset amenity counts to 0 when returning to page 1
    if "amenity_counts_committed" in st.session_state:
        st.session_state.amenity_counts_committed = {
            amenity: 0 for amenity in st.session_state.amenity_counts_committed
        }
    
    f.initialize_game()

    if st.button("Next", key="page1_next"):
        st.session_state.page = 2

elif st.session_state.page == 2:

    f.prev_week_results()

    if st.button("Next", key="page2_next"):
        st.session_state.page = 3

elif st.session_state.page == 3:

    total_FAR_Bonus, selected_amenities, amenity_counts = f.amenity_select_sidebar()
    f.amenity_select_main(total_FAR_Bonus, selected_amenities, amenity_counts)
    f.proforma_inputs_updater(total_FAR_Bonus, selected_amenities, amenity_counts)

    # Always save current values to session_state so they persist to page 4
    st.session_state.total_FAR_Bonus = total_FAR_Bonus
    st.session_state.selected_amenities = selected_amenities
    st.session_state.amenity_counts = amenity_counts

    if st.button("Next", key="page3_next"):
        # Commit amenity counts (become minimums for next selection round)
        st.session_state.amenity_counts_committed = amenity_counts.copy()
        st.session_state.page = 4

elif st.session_state.page == 4:

    # Retrieve values saved from page 3
    total_FAR_Bonus = st.session_state.get("total_FAR_Bonus", 0)
    selected_amenities = st.session_state.get("selected_amenities", [])
    amenity_counts = st.session_state.get("amenity_counts", {})

    st.write("Page 4")
    f.proforma_inputs_updater(total_FAR_Bonus, selected_amenities, amenity_counts)
    proforma_table = f.run_proforma(total_FAR_Bonus, selected_amenities, amenity_counts)
    st.write(proforma_table)
    irr, npv = f.profit_calculator(proforma_table)
    st.write("IRR:", irr)
    st.write("NPV:", npv)

    if st.button("Next", key="page4_next"):
        # After page 4, loop back to page 1
        st.session_state.page = 5

elif st.session_state.page == 5:
    f.second_developer_cycle()
    if st.button("Next", key="page5_next"):
        # After page 4, loop back to page 1
        st.session_state.page = 6

elif st.session_state.page == 6:
    total_FAR_Bonus, selected_amenities, amenity_counts = f.amenity_select_sidebar()
    f.amenity_select_main(total_FAR_Bonus, selected_amenities, amenity_counts)
    f.proforma_inputs_updater(total_FAR_Bonus, selected_amenities, amenity_counts)

    # Always save current values to session_state so they persist
    st.session_state.total_FAR_Bonus = total_FAR_Bonus
    st.session_state.selected_amenities = selected_amenities
    st.session_state.amenity_counts = amenity_counts

    if st.button("Next", key="page6_next"):
        # Commit amenity counts (become minimums for next selection round)
        st.session_state.amenity_counts_committed = amenity_counts.copy()
        st.session_state.page = 7

elif st.session_state.page == 7:

    # Retrieve values saved from page 6
    total_FAR_Bonus = st.session_state.get("total_FAR_Bonus", 0)
    selected_amenities = st.session_state.get("selected_amenities", [])
    amenity_counts = st.session_state.get("amenity_counts", {})

    st.write("Page 7")
    f.proforma_inputs_updater(total_FAR_Bonus, selected_amenities, amenity_counts)
    proforma_table = f.run_proforma(total_FAR_Bonus, selected_amenities, amenity_counts)
    st.write(proforma_table)
    irr, npv = f.profit_calculator(proforma_table)
    st.write("IRR:", irr)
    st.write("NPV:", npv)

    if st.button("Start Over", key="page7_next"):
        # Commit amenity counts (become minimums for next selection round)
        st.session_state.page = 1