import Spec

namespace EGcdNarrowProbe

def width (n : Nat) : Nat := n+1
def bits (n : Nat) : Nat := width n*(n+1)
def modulus (n : Nat) : Nat := 1 <<< bits n

def den (n w M : Nat) : Nat → Nat
  | 0 => 1
  | k+1 => (den n w M k * (M+1-(1 <<< (w*(k+1))))) % M

def inv (a M : Nat) : Nat :=
  let r := Nat.extendedGcd a M
  (r.coeffA % (M : Int)).toNat

def packed (n : Nat) : Nat :=
  let w := width n
  let M := modulus n
  inv (den n w M n) M

def impl (n : Nat) : Nat :=
  packed n / (1 <<< (width n*n)) % (1 <<< width n)

end EGcdNarrowProbe
