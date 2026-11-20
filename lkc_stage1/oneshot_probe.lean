import Spec

namespace OneShotProbe

def width (n : Nat) : Nat := 2 * n + 1
def rowMod (n : Nat) : Nat := 1 <<< (width n * (n + 1))

def numerProd (n w : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 =>
      numerProd n w k *
        ((1 <<< (w * (k + 1) * (n / (k + 1) + 1))) - 1)

def denomProd (w : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 =>
      denomProd w k * ((1 <<< (w * (k + 1))) - 1)

def packedRow (n : Nat) : Nat :=
  numerProd n (width n) n / denomProd (width n) n % rowMod n

def impl (n : Nat) : Nat :=
  packedRow n / (1 <<< (width n * n)) % (1 <<< width n)

end OneShotProbe
