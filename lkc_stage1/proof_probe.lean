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

theorem fin_sub_one_nat (M a : Nat) [NeZero M] (hM : 1 < M)
    (ha0 : 0 < a) (haM : a < M) :
    Fin.ofNat M a - 1 = Fin.ofNat M (a - 1) := by
  apply Fin.ext
  change (a % M + (M - (1 % M))) % M = (a - 1) % M
  rw [Nat.mod_eq_of_lt haM, Nat.mod_eq_of_lt hM]
  have hsum : a + (M - 1) = M + (a - 1) := by omega
  rw [hsum, Nat.add_mod_self_left, Nat.mod_eq_of_lt (by omega : a - 1 < M)]

theorem fin_pow64_zero (M x : Nat) [NeZero M]
    (h : x ^ 64 % M = 0) :
    (Fin.ofNat M x) ^ 64 = 0 := by
  apply Fin.ext
  change (x % M) ^ 64 % M = 0
  rw [← Nat.pow_mod]
  exact h

end ProofProbe
