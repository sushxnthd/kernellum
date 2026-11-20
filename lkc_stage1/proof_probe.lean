import Spec

namespace ProofProbe

theorem fin_tel_step {M : Nat} [NeZero M] (z : Fin M) :
    (1 + z) * (1 - z) = 1 - z * z := by
  simp [sub_eq_add_neg, add_mul, mul_add]

end ProofProbe
