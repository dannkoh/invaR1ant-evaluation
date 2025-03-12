def generate_constraints(N: int) -> str:
    # Build a list of individual comparison constraints.
    parts = []
    
    # 1. Enforce a strict ordering among the inputs: for each pair (in0, ..., in{N-1}),
    # every later input must be greater than every earlier input.
    for i in range(1, N):
        for j in range(0, i):
            parts.append(f"(> in{i} in{j})")
            
    # 2. Enforce that the free input 'in' is greater than each input.
    for i in range(N):
        parts.append(f"(> in in{i})")
        
    # If no constraints were generated (e.g. N == 0), just return a trivial assertion.
    if not parts:
        return "(assert true)"
    
    # Combine the individual comparisons into a nested, left-associative "and" expression.
    # This produces a structure similar to the examples provided.
    nested = parts[0]
    for part in parts[1:]:
        nested = f"(and {nested} {part})"
    
    # Return the final SMT-LIB format constraint string.
    return f"(assert {nested})"

N = int(input("N="))
constraints = generate_constraints(N)
with open("test.smt2", "w") as f:
    constants = "\n".join([f"(declare-const in{i} Int)" for i in range(1000)])
    constants += "\n(declare-const in Int)"
    f.write(f"{constants}\n{constraints}\n(check-sat)\n(get-model)\n")
