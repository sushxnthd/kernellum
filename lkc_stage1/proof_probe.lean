import Spec

namespace ProofProbe

def telFin {M : Nat} [NeZero M] (a : Fin M) : Fin M :=
  let y := a - 1
  let z2 := y * y
  let a2 := (1 - y) * (1 + z2)
  let z4 := z2 * z2
  let a4 := a2 * (1 + z4)
  let z8 := z4 * z4
  let a8 := a4 * (1 + z8)
  let z16 := z8 * z8
  let a16 := a8 * (1 + z16)
  let z32 := z16 * z16
  a16 * (1 + z32)

theorem fin_tel64 {M : Nat} [NeZero M] (a : Fin M) :
    a * telFin a = 1 - (a - 1) ^ 64 := by
  unfold telFin
  grind

theorem fin_nat_sub_repr (M y : Nat) [NeZero M] (hM : 1 < M) (hy : y < M) :
    Fin.ofNat M (M + 1 - y) = (1 : Fin M) - Fin.ofNat M y := by
  apply Fin.ext
  simp [Fin.ofNat, Fin.sub]
  grind

theorem mask_pow_mod (x e : Nat) :
    x &&& ((1 <<< e) - 1) = x % (1 <<< e) := by
  rw [Nat.shiftLeft_eq, Nat.one_mul, Nat.and_two_pow_sub_one_eq_mod]

end ProofProbe
