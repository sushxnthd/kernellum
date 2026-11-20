import Spec
namespace Newton6ModProbe
def width (n : Nat) : Nat := 2*n+1
def bits (n : Nat) : Nat := width n*(n+1)
def modulus (n : Nat) : Nat := 1 <<< bits n
def den (n w M : Nat) : Nat → Nat
| 0 => 1
| k+1 => (den n w M k * (M+1-(1 <<< (w*(k+1))))) % M
def step (a M x : Nat) : Nat := (x*(M+2-((a*x)%M)))%M
def loop (a M : Nat) : Nat → Nat → Nat
| 0,x=>x
| t+1,x=>loop a M t (step a M x)
def packed (n:Nat):Nat := let w:=width n; let M:=modulus n; loop (den n w M n) M 6 1
def impl (n:Nat):Nat := packed n / (1 <<< (width n*n)) % (1 <<< width n)
end Newton6ModProbe
