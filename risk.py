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
    #TODO: your job, see below
    raise NotImplementedError

if __name__ == "__main__":
    print(round(wet_bulb(20, 50), 1))
    print(round(thi(30, 60), 1))