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

theorem fin_complement (M y : Nat) [NeZero M] (hM : 1 < M) (hy : y < M) :
    Fin.ofNat M (M + 1 - y) + Fin.ofNat M y = 1 := by
  apply Fin.ext
  change (((M + 1 - y) % M + y % M) % M) = 1 % M
  rw [← Nat.add_mod]
  rw [show M + 1 - y + y = M + 1 by omega]
  simp [Nat.mod_eq_of_lt hM]

theorem fin_succ_repr (M a : Nat) [NeZero M] (hM : 1 < M)
    (ha0 : 0 < a) (haM : a < M) :
    Fin.ofNat M a = 1 + Fin.ofNat M (a - 1) := by
  apply Fin.ext
  change a % M = ((1 % M + (a - 1) % M) % M)
  rw [← Nat.add_mod, show 1 + (a - 1) = a by omega]

theorem fin_complement_eq_sub (M y : Nat) [NeZero M] (hM : 1 < M) (hy : y < M) :
    Fin.ofNat M (M + 1 - y) = (1 : Fin M) - Fin.ofNat M y := by
  have hc := fin_complement M y hM hy
  grind

theorem fin_ofNat_mod (M x : Nat) [NeZero M] :
    Fin.ofNat M (x % M) = Fin.ofNat M x := by
  apply Fin.ext
  simp [Fin.ofNat]

theorem fin_ofNat_add (M x y : Nat) [NeZero M] :
    Fin.ofNat M (x + y) = Fin.ofNat M x + Fin.ofNat M y := by
  apply Fin.ext
  simp [Fin.ofNat, Nat.add_mod]

theorem fin_ofNat_mul (M x y : Nat) [NeZero M] :
    Fin.ofNat M (x * y) = Fin.ofNat M x * Fin.ofNat M y := by
  apply Fin.ext
  simp [Fin.ofNat, Nat.mul_mod]

def telMod (M a : Nat) : Nat :=
  let y := a - 1
  let z2 := (y * y) % M
  let a2 := ((M + 1 - y) * (1 + z2)) % M
  let z4 := (z2 * z2) % M
  let a4 := (a2 * (1 + z4)) % M
  let z8 := (z4 * z4) % M
  let a8 := (a4 * (1 + z8)) % M
  let z16 := (z8 * z8) % M
  let a16 := (a8 * (1 + z16)) % M
  let z32 := (z16 * z16) % M
  (a16 * (1 + z32)) % M

theorem telMod_fin (M a : Nat) [NeZero M] (hM : 1 < M)
    (ha0 : 0 < a) (haM : a < M) :
    Fin.ofNat M (telMod M a) = telFin (Fin.ofNat M a) := by
  unfold telMod telFin
  rw [fin_succ_repr M a hM ha0 haM]
  rw [fin_complement_eq_sub M (a - 1) hM (by omega)]
  simp only [fin_ofNat_mod, fin_ofNat_add, fin_ofNat_mul]
  rfl

theorem mask_pow_mod (x e : Nat) :
    x &&& ((1 <<< e) - 1) = x % (1 <<< e) := by
  rw [Nat.shiftLeft_eq, Nat.one_mul, Nat.and_two_pow_sub_one_eq_mod]

end ProofProbe
