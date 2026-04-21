"""
Test BKT (Bayesian Knowledge Tracing) implementation.
"""
import sys
sys.path.insert(0, 'src')

from src.services.bkt_impl import BKT

print("=== BKT Service Test ===\n")

# Create BKT instance with standard parameters
print("Creating BKT with parameters:")
print("  P(L0) = 0.10 (initial mastery)")
print("  P(T)  = 0.50 (learning probability)")
print("  P(S)  = 0.20 (slip probability)")
print("  P(G)  = 0.25 (guess probability)\n")

bkt = BKT(p_l0=0.10, p_trans=0.50, p_slip=0.20, p_guess=0.25)
print(f"Initial P(mastery): {bkt.p_l:.4f}\n")

# Simulate student responses
print("Simulating student responses:")
responses = [
    (True, "Correct - student answers correctly"),
    (True, "Correct - student answers correctly again"),
    (False, "Incorrect - student makes a mistake"),
    (True, "Correct - student recovers"),
    (True, "Correct - student masters the skill"),
]

for is_correct, description in responses:
    old_p = bkt.p_l
    bkt.forward_inference(is_correct=is_correct)
    direction = "↑" if bkt.p_l > old_p else "↓" if bkt.p_l < old_p else "→"
    print(f"  {description}: P(mastery) {old_p:.4f} {direction} {bkt.p_l:.4f}")

print(f"\nFinal P(mastery): {bkt.p_l:.4f}")
print(f"Predicted P(correct response): {bkt.predict_probability():.4f}")

# Get node state
state = bkt.get_node("4.OA.A.1")
print(f"\nBKT Node State:")
print(f"  P(L0) = {state.p_l0:.2f}")
print(f"  P(T)  = {state.p_trans:.2f}")
print(f"  P(S)  = {state.p_slip:.2f}")
print(f"  P(G)  = {state.p_guess:.2f}")
print(f"  P(L)  = {state.p_l:.4f}")

# Classification
print("\nMastery Classification:")
if bkt.p_l >= 0.80:
    print("  HIGH - Student has mastered this skill")
elif bkt.p_l >= 0.60:
    print("  MEDIUM - Student is approaching mastery")
else:
    print("  LOW - Student needs more practice")
