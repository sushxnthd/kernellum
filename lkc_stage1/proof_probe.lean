import Spec

namespace ProofProbe

theorem fin_tel_step {M : Nat} [NeZero M] (z : Fin M) :
    (1 + z) * (1 - z) = 1 - z * z := by
  grind

theorem nat_tel_step (M y : Nat) (hM : 1 < M) (hy : y < M) :
    ((1 + y) * (M + 1 - y)) % M
      = (M + 1 - ((y * y) % M)) % M := by
  grind

theorem mask_pow_mod (x e : Nat) :
    x &&& ((1 <<< e) - 1) = x % (1 <<< e) := by
  rw [Nat.shiftLeft_eq, Nat.one_mul, Nat.and_two_pow_sub_one_eq_mod]

end ProofProbe
