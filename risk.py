import math 

def wet_bulb(temp_c, rh):
    #Stull (2011) approximation. Valid roughly for RH 5-99% and sea-level pressure.
    return (
        temp_c * math.atan(0.151977 * (rh + 8.313659) ** 0.5)
        + math.atan(temp_c + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
        - 4.686035
    )

def thi(temp_c, rh):
    # Broiler THI as reported from Tao and Xin (2003): 0.85 * dry bulb + 0.15 * wet bulb
    return 0.85 * temp_c + 0.15 * wet_bulb(temp_c, rh)

# (body weight in kg, THI where body temperature starts rising)
# Copied from a summary. Verify against the paper's tables before trusting.
ONSET_POINTS = [(1.5, 25.7), (2.5, 22.6), (3.0, 21.1)]

def onset_thi_for_weight(weight_kg):
    points = ONSET_POINTS
    if weight_kg <= points[0][0]:
        return points[0][1]
    if weight_kg >= points[-1][0]:
        return points[-1][1]
    for (w1, t1), (w2, t2) in zip(points, points[1:]):
        if w1 <= weight_kg <= w2:
            return t1 + (weight_kg - w1) * (t2 - t1) / (w2 - w1)

AGE_WEIGHT_POINTS = [(1, 0.045), (7, 0.18), (14, 0.46), (21, 0.875), (28, 1.55), (42, 2.85)]
def age_to_weight(age_days):
    points = AGE_WEIGHT_POINTS
    if age_days <= points[0][0]:
        return points[0][1]
    if age_days >= points[-1][0]:
        return points[-1][0]
    for (a1, w1), (a2, w2) in zip(points, points[1:]):
        if a1 <= age_days <= a2:
            return w1 + (age_days - a1) * (w2 - w1) / (a2 - a1)

BAND = 2.0

ACTIONS = {
    "Normal": "No action needed. Keep fresh water available.",
    "Watch": "Approach the stress point. Check ventilation and water now.",
    "High": "Birds are likely stressed. Increase airflow, give cool water, keep birds calm.",
    "Critical": "Serious risk of heat exhaustion. Cool the house now and avoid handling birds.",
}

def risk_tier(temp_c, rh, weight_kg):
    gap = thi(temp_c, rh) - onset_thi_for_weight(weight_kg)
    if gap < -BAND:
        tier = "Normal"
    elif gap <= 0:
        tier = "Watch"
    elif gap <= BAND:
        tier = "High"
    else:
        tier = "Critical"
    return {"tier": tier, "gap": round(gap, 2), "action": ACTIONS[tier]}


if __name__ == "__main__":
    print(round(wet_bulb(20, 50), 1))
    print(round(thi(30, 60), 1))
    print(round(onset_thi_for_weight(2.0), 2))
    print(round(onset_thi_for_weight(1.0), 2))
    print(round(onset_thi_for_weight(3.5), 2))