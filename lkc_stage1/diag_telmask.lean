import Spec
namespace Submission
def width (n : Nat) : Nat := 2*n+1
def bits (n : Nat) : Nat := width n*(n+1)
def modulus (n : Nat) : Nat := 1 <<< bits n
def red (M x:Nat):Nat := x &&& (M-1)
def den (n w M : Nat) : Nat → Nat
| 0 => 1
| k+1 => red M (den n w M k * (M+1-(1 <<< (w*(k+1)))))
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
def packed (n:Nat):Nat := let w:=width n; let M:=modulus n; inv64 M (den n w M n)
def impl (n:Nat):Nat := (packed n / (1 <<< (width n*n))) &&& ((1 <<< width n)-1)
end Submission
