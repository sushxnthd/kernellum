import Spec

namespace ProofProbe

theorem fin_tel_step {M : Nat} [NeZero M] (z : Fin M) :
    (1 + z) * (1 - z) = 1 - z * z := by
  grind

end ProofProbe
