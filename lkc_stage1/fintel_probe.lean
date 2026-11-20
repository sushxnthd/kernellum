import Spec
namespace FinTelProbe

def width (n : Nat) : Nat := 2*n+1
def bits (n : Nat) : Nat := width n*(n+1)
def modulus (n : Nat) : Nat := 1 <<< bits n

def red (M x:Nat):Nat := x &&& (M-1)
def factor (n w M k : Nat) : Nat := M+1-(1 <<< (w*k))
def den (n w M : Nat) : Nat → Nat
| 0 => 1
| k+1 => red M (den n w M k * factor n w M (k+1))

def telFin {M : Nat} [NeZero M] (a : Fin M) : Fin M :=
  let y := a - 1
  let z2 := y*y
  let a2 := (1-y)*(1+z2)
  let z4 := z2*z2
  let a4 := a2*(1+z4)
  let z8 := z4*z4
  let a8 := a4*(1+z8)
  let z16 := z8*z8
  let a16 := a8*(1+z16)
  let z32 := z16*z16
  a16*(1+z32)

def packed (n:Nat):Nat :=
  let M := modulus n
  letI : NeZero M := ⟨by
    unfold M modulus
    rw [Nat.shiftLeft_eq, Nat.one_mul]
    exact Nat.ne_of_gt (Nat.pow_pos (by omega))⟩
  (telFin (Fin.ofNat M (den n (width n) M n))).val

def impl (n:Nat):Nat :=
  packed n / (1 <<< (width n*n)) % (1 <<< width n)

end FinTelProbe
