import Spec

namespace NewtonNarrowProbe

def width (n : Nat) : Nat := n + 1
def bits (n : Nat) : Nat := width n * (n + 1)
def modulus (n : Nat) : Nat := 1 <<< bits n

def denProdMod (n w M : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 =>
      (denProdMod n w M k *
        (M + 1 - (1 <<< (w * (k + 1))))) % M

def invStep (a M x : Nat) : Nat :=
  (x * (M + 2 - ((a * x) % M))) % M

def invLoop (a M : Nat) : Nat → Nat → Nat
  | 0, x => x
  | t + 1, x => invLoop a M t (invStep a M x)

def packed (n : Nat) : Nat :=
  let w := width n
  let M := modulus n
  let a := denProdMod n w M n
  invLoop a M (Nat.log2 (bits n) + 1) 1

def impl (n : Nat) : Nat :=
  packed n / (1 <<< (width n * n)) % (1 <<< width n)

end NewtonNarrowProbe
