import functions as f
import data as d
import streamlit as st

st.session_state.setdefault("page", 1)

st.set_page_config(page_title="Week 3 Developer Game", page_icon=":building_construction:", layout="wide")

# Widen the sidebar
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 420px;
        max-width: 420px;
    }
    </style>
    """, unsafe_allow_html=True)

# Compute FAR bonuses once on every rerun so d.amenity_menu is always up to date
d.amenity_menu = f.FAR_bonus_menu()

if st.session_state.page == 1:
    
    # Reset amenity counts to 0 when returning to page 1
    if "amenity_counts_committed" in st.session_state:
        st.session_state.amenity_counts_committed = {
            amenity: 0 for amenity in st.session_state.amenity_counts_committed
        }
    
    # Clear all per-round summary data so the summary page starts fresh
    for _key in [
        "total_FAR_Bonus", "total_FAR_Bonus_round1", "total_FAR_Bonus_round2",
        "selected_amenities", "selected_amenities_round1",
        "amenity_counts", "amenity_counts_round1", "amenity_counts_round2", "amenity_counts_round2_delta",
        "irr_round1", "npv_round1", "irr_round2", "npv_round2",
    ]:
        st.session_state.pop(_key, None)
    # Clear round 2 sidebar widget state so page 6 starts with blank selection
    for _name in d.amenity_menu["Amenity"]:
        st.session_state.pop(f"amenity_round2_{_name}", None)

    f.initialize_game()

    if st.button("Next", key="page1_next"):
        st.session_state.page = 2

elif st.session_state.page == 2:

    f.prev_week_results()

    if st.button("Next", key="page2_next"):
        st.session_state.page = 3

elif st.session_state.page == 3:

    total_FAR_Bonus, incremental_FAR_Bonus, selected_amenities, amenity_counts, _, _ = f.amenity_select_sidebar(is_round2=False)
    f.amenity_select_main(incremental_FAR_Bonus, selected_amenities, amenity_counts)
    f.proforma_inputs_updater(total_FAR_Bonus, selected_amenities, amenity_counts)

    st.session_state.total_FAR_Bonus = total_FAR_Bonus
    st.session_state.total_FAR_Bonus_round1 = incremental_FAR_Bonus
    st.session_state.selected_amenities = selected_amenities
    st.session_state.selected_amenities_round1 = selected_amenities
    st.session_state.amenity_counts = amenity_counts

    if st.button("Next", key="page3_next"):
        st.session_state.amenity_counts_committed = amenity_counts.copy()
        st.session_state.amenity_counts_round1 = amenity_counts.copy()
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

    # Persist round 1 results for the summary page
    st.session_state.irr_round1 = irr
    st.session_state.npv_round1 = npv

    if st.button("Next", key="page4_next"):
        st.session_state.page = 5

elif st.session_state.page == 5:
    f.second_developer_cycle()
    if st.button("Next", key="page5_next"):
        # Clear round 2 sidebar state so page 6 starts with blank selection
        for _name in d.amenity_menu["Amenity"]:
            st.session_state.pop(f"amenity_round2_{_name}", None)
        st.session_state.page = 6

elif st.session_state.page == 6:
    total_FAR_Bonus, incremental_FAR_Bonus, selected_this_round, counts_this_round, selected_cumulative, counts_cumulative = f.amenity_select_sidebar(is_round2=True)
    # Main area: show only this cycle's selection (starts blank)
    f.amenity_select_main(incremental_FAR_Bonus, selected_this_round, counts_this_round)
    # Pro forma uses cumulative for building specs
    f.proforma_inputs_updater(total_FAR_Bonus, selected_cumulative, counts_cumulative)

    st.session_state.total_FAR_Bonus = total_FAR_Bonus
    st.session_state.total_FAR_Bonus_round2 = incremental_FAR_Bonus
    st.session_state.selected_amenities = selected_cumulative
    st.session_state.amenity_counts = counts_cumulative

    if st.button("Next", key="page6_next"):
        st.session_state.amenity_counts_round2 = counts_this_round
        st.session_state.amenity_counts_round2_delta = counts_this_round
        st.session_state.amenity_counts_committed = counts_cumulative.copy()
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

    # Persist round 2 results for the summary page
    st.session_state.irr_round2 = irr
    st.session_state.npv_round2 = npv

    if st.button("Next", key="page7_next"):
        st.session_state.page = 8

elif st.session_state.page == 8:
    f.game_summary()

    if st.button("Start Over", key="page8_restart"):
        st.session_state.page = 1