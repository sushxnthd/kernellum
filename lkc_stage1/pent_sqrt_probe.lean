import Spec
namespace PentSqrtProbe

def width (n : Nat) : Nat := max 1 (3 * Nat.sqrt n)
def modulus (n : Nat) : Nat := 1 <<< (width n*(n+1))
def red (M x:Nat):Nat := x &&& (M-1)
def bt (n e : Nat) : Nat := if e ≤ n then 1 <<< (width n * e) else 0
def pentDen (n : Nat) : Nat :=
  let M := modulus n
  let pos := 1 + bt n 5 + bt n 7 + bt n 22 + bt n 26 + bt n 51 + bt n 57
  let neg := bt n 1 + bt n 2 + bt n 12 + bt n 15 + bt n 35 + bt n 40
  red M (M + pos - neg)
def inv64 (M a : Nat) : Nat :=
  let y := a - 1
  let z2 := red M (y*y)
  let a2 := red M ((M+1-y) * (1+z2))
  let z4 := red M (z2*z2)
  let a4 := red M (a2 * (1+z4))
  let z8 := red M (z4*z4)
  let a8 := red M (a4 * (1+z8))
  let z16 := red M (z8*z8)
  let a16 := red M (a8 * (1+z16))
  let z32 := red M (z16*z16)
  red M (a16 * (1+z32))
def packed (n:Nat):Nat := inv64 (modulus n) (pentDen n)
def impl (n:Nat):Nat := (packed n / (1 <<< (width n*n))) &&& ((1 <<< width n)-1)
end PentSqrtProbe
