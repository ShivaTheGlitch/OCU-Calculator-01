import streamlit as st
import math

# -----------------------------------------------
# Pressure Drop Lookup Table (phase velocity → Pa)
# -----------------------------------------------
pressure_drop_table = {
    0.10: 400, 0.11: 500, 0.12: 600, 0.13: 700, 0.14: 800,
    0.15: 900, 0.16: 950, 0.17: 1000, 0.18: 1050, 0.19: 1150,
    0.20: 1200, 0.21: 1300, 0.22: 1400, 0.23: 1500, 0.24: 1700,
    0.25: 1800, 0.26: 1850, 0.27: 1900, 0.28: 1950, 0.29: 2000,
    0.30: 2150, 0.31: 2200, 0.32: 2300, 0.33: 2400, 0.34: 2550,
    0.35: 2600, 0.36: 2750, 0.37: 2800, 0.38: 2950, 0.39: 3250,
    0.40: 3500
}

# -----------------------------------------------
# Vessel dimensions (Dia, Height)
# -----------------------------------------------
vessels = [
    (0.7, 1.2),
    (0.9, 1.6),
    (1.2, 1.6),
    (1.4, 1.6),
    (1.6, 1.8),
    (1.8, 1.8),
    (1.9, 1.8),
    (2.0, 1.8),
    (2.2, 1.8),
    (2.4, 1.8)
]


# -----------------------------------------------
# Streamlit App
# -----------------------------------------------
st.title("🟩 OCU Capacity, Vessel Design & Pressure Drop Calculator")
st.write("Complete engineering calculator for Odour Control Units")

# ---------------------------------------------------
# Part 1 – Tank Capacity Calculation
# ---------------------------------------------------
st.header("📌 Part 1 — Tank Capacity Calculation")

ach = st.number_input("Enter ACH (Air Changes per Hour):", min_value=1.0, max_value=50.0)

tank_types = {
    "Bar Screen Chamber": "height",
    "Oil & Grease Trap": "height",
    "Equalization Tank": "et",
    "Sludge Holding Tank": "sht"
}

add_tank = st.checkbox("Add tanks")

tanks = []
total_flow = 0

if add_tank:
    for tname, ttype in tank_types.items():
        st.subheader(tname)
        l = st.number_input(f"{tname} Length (m)", key=f"{tname}_L", value=1.0)
        b = st.number_input(f"{tname} Breadth (m)", key=f"{tname}_B", value=1.0)
        h = st.number_input(f"{tname} Total Height (m)", key=f"{tname}_H", value=1.0)

        if ttype == "height":
            freeboard = h
        elif ttype == "et":
            opt = st.radio(f"Equalization Tank freeboard rule:", ["Height - 1", "Height / 2"], key=f"{tname}_rule")
            freeboard = h - 1 if opt == "Height - 1" else h / 2
        else:   # Sludge Holding Tank
            freeboard = 1.0

        fb_vol = l * b * freeboard
        flow = fb_vol * ach
        total_flow += flow

        tanks.append({
            "Tank": tname,
            "Dimensions": f"{l} × {b} × {h}",
            "Freeboard": freeboard,
            "FB Volume": fb_vol,
            "Flowrate": flow
        })

# Display table
if len(tanks) > 0:
    st.subheader("📊 Tank Flowrate Table")
    st.table(tanks)

def next_multiple_of_50(value):
    return int(((value + 49) // 50) * 50)

ocu_capacity = next_multiple_of_50(total_flow)
st.success(f"Total Flowrate = **{total_flow:.2f} m³/hr**")
st.success(f"OCU Required Capacity = **{ocu_capacity} m³/hr**")


# ---------------------------------------------------
# Part 2 — Vessel Selection & Media Quantity
# ---------------------------------------------------
st.header("📌 Part 2 — Vessel Design")

flow_m3hr = total_flow
flow_m3sec = flow_m3hr / 3600

CT = st.number_input("Enter Contact Time (sec):", min_value=1.0, value=30.0)

media_volume = flow_m3sec * CT

# vessel selection logic
min_H = 0.6
max_H = 0.8

selected_vessel = None
selected_H = None

for dia, h in vessels:
    area = math.pi * (dia/2)**2
    H = media_volume / area
    if min_H <= H <= max_H:
        selected_vessel = (dia, h)
        selected_H = H
        break

# If too low, choose smallest vessel
if selected_vessel is None:
    dia, h = vessels[0]
    area = math.pi * (dia/2)**2
    selected_H = media_volume / area
    selected_vessel = (dia, h)

st.subheader("🛢 Selected Vessel")
st.write(f"Diameter: **{selected_vessel[0]} m**")
st.write(f"Shell Height: **{selected_vessel[1]} m**")
st.write(f"Bed Height: **{selected_H:.3f} m**")
st.write(f"Media Volume: **{media_volume:.3f} m³**")

# ---------------------------------------------------
# Part 3 — Media Quantity (bags of 25kg)
# ---------------------------------------------------
st.header("📌 Activated Carbon Media Quantity")

carbon_kg = media_volume * 500
bags_25kg = math.ceil(carbon_kg / 25) * 25

st.write(f"Required Carbon Media = **{carbon_kg:.1f} kg**")
st.success(f"Carbon Required in 25 kg bags = **{bags_25kg} kg**")


# ---------------------------------------------------
# Part 4 — Pressure Drop Calculation
# ---------------------------------------------------
st.header("📌 Pressure Drop Calculation")

dia = selected_vessel[0]
area = math.pi * (dia/2)**2

# Correct formula
phase_velocity = flow_m3sec / area
phase_velocity = round(phase_velocity, 2)

# Pressure drop lookup
matched_key = min(pressure_drop_table.keys(), key=lambda x: abs(x - phase_velocity))
dp_bed_per_m = pressure_drop_table[matched_key]

dp_bed = dp_bed_per_m * selected_H
dp_prefilter = 65
dp_duct = 100
dp_suction = 300

total_dp = dp_bed + dp_prefilter + dp_duct + dp_suction

st.write(f"Phase Velocity = **{phase_velocity} m/s**")
st.write(f"Pressure Drop Across Bed/m = **{dp_bed_per_m} Pa**")
st.write(f"Pressure Drop Across Media = **{dp_bed:.0f} Pa**")
st.write(f"Prefilter Loss = **65 Pa**")
st.write(f"Duct & Fittings = **100 Pa**")
st.write(f"Suction Loss = **300 Pa**")

st.success(f"Total Pressure Drop = **{total_dp:.0f} Pa**")

# Fan selection
if total_dp < 1700:
    st.info("Recommended Fan Type: **PP Fan**")
else:
    st.warning("Recommended Fan Type: **FRP Fan (High Pressure)**")

