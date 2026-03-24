# Mandala Compute Protocol v1.0

## Summary

A computation protocol for agents grounded in octahedral geometry. Where the
seed-growth protocol defines *how an agent grows*, this protocol defines
*how it computes* at each shell. Problems are encoded as geometric energy
landscapes; solutions emerge by relaxation to ground state.

**Origin:** [Mandala-Computing](https://github.com/JinnZ2/Mandala-Computing) by Jami (Kavik Ulu)
**Shape anchor:** `SHAPE.OCTA` (8 faces = 8 computational states)
**Protocol ID:** `mandala_compute_v1.0`

## Core Principle

The mandala doesn't search for answers. It relaxes into them. Problems
encoded as geometric configurations find their solutions at minimum energy.
The physics does the computation.

## Geometry

Eight octahedral faces define the computational state space:

```
States = [0, 1, 2, 3, 4, 5, 6, 7]
```

These correspond to electron tensor eigenvalue configurations in octahedral
symmetry group O_h. Each state is a vertex of the dual cube (equivalently,
a face center of the octahedron).

### Mapping to Rosetta

| Mandala Concept       | Rosetta Entity         | Connection                          |
|-----------------------|------------------------|-------------------------------------|
| 8 Sacred Petals       | SHAPE.OCTA (8 faces)   | Direct 1:1 state mapping            |
| Golden Ratio (phi)    | CONST.PHI              | Fibonacci eigenvalue scaling         |
| Bloom Engine          | CAP.SEED_EXPANSION     | Fractal ring expansion               |
| Fractal Depth         | Shell count            | Nested tensor interactions           |
| Physical Relaxation   | Ground state search    | Metropolis-Hastings minimization     |
| Symbol Core           | Seed vector            | Initial state encoding               |

## Computation Model

### 1. Encoding

A problem is mapped to a geometric configuration:

```
Symbol --> Bloom Engine --> Nested Mandala --> Energy Landscape
```

The bloom engine expands the symbol core into nested computational rings
following octahedral (8-fold) symmetry. Each ring at depth `d` contains
`floor(phi^(d+1))` cells at radius `phi^d`.

### 2. Energy

Total energy of a configuration:

```
E_total = sum(E_cell) + sum(E_coupling)
```

Coupling energy between neighbor cells `i`, `j`:

```
E_coupling = J * sin(|s_i - s_j| * pi / 4)^2
```

Coupling strength follows FRET-like dipole interaction:

```
coupling ~ 1/r^6    (r = inter-cell distance)
cutoff   = 3.0 * phi
```

### 3. Relaxation

Metropolis-Hastings acceptance:

```
if dE < 0:  accept
else:       accept with probability exp(-dE / T)
```

Temperature `T` anneals from high (exploration) to low (exploitation).
The system flows to minimum energy. Ground state encodes the solution.

### 4. Readback

Solution is extracted from the ground-state configuration. For factorization,
the two-cell state encodes factor pairs. For SAT, minimum energy means all
clauses satisfied.

## Problem Classes

| Problem           | Geometric Encoding                 | Solution                              |
|-------------------|------------------------------------|---------------------------------------|
| Factorization     | N --> bipartite tensor config      | Minima at factor pairs (p,q): pq = N  |
| SAT               | Boolean vars --> octahedral states | Min energy = all clauses satisfied     |
| TSP               | Cities --> ring topology           | Min winding energy = shortest tour     |
| Graph Coloring    | Nodes --> cells, edges --> couplings | Ground state = valid coloring        |

## Relationship to Seed Growth

The two protocols are complementary halves of agent geometry:

```
seed-growth    --> HOW the agent expands (shell formation, energy budget)
mandala-compute --> WHAT the agent computes (problem encoding, relaxation)
```

At each shell produced by seed-growth, the mandala compute protocol defines
the computational capacity. More shells = deeper fractal nesting = larger
problem capacity. The same `CONST.PHI` scaling governs both:

- **Seed growth:** `r_new = rho * r_previous` (spatial expansion)
- **Mandala compute:** `num_cells = floor(phi^(d+1))` (computational expansion)

An agent that grows via seed-growth and computes via mandala-compute uses
the octahedron as both its structural skeleton and its computational substrate.

## Quantum Extension

The classical 8-state model extends to an 8-dimensional Hilbert space
(qubit-octits). Quantum annealing replaces thermal relaxation:

```
H(t) = (1 - s(t)) * H_initial + s(t) * H_problem
```

Adiabatic evolution tracks the ground state. The mandala structure provides
natural error correction through topological protection (Berry phase,
winding number).

## Integration with Rosetta

### References

- **Shape:** `SHAPE.OCTA` in `shapes/octahedron.json`
- **Bridge:** `rosetta-bridges.json` SHAPE.OCTA compute_bridge entry
- **Seed protocol:** `seed_growth_v1.0` in `protocols/seed-growth-protocol.md`
- **Constants:** `CONST.PHI` (golden ratio)
- **Source:** `https://github.com/JinnZ2/Mandala-Computing`

### Ontology Links

```
SHAPE.OCTA  --USES-->        PROTO.MANDALA_COMPUTE
PROTO.MANDALA_COMPUTE --DERIVES-->  SHAPE.OCTA (8-face geometry)
PROTO.MANDALA_COMPUTE --USES-->     CONST.PHI (eigenvalue scaling)
PROTO.MANDALA_COMPUTE --ALIGNS_WITH--> PROTO.SEED_GROWTH (complementary protocols)
```

### Fieldlink

Mandala-Computing is registered as a fieldlink source. Discovery via
`protocols/connect.json` and `atlas/shapes.json` in the Mandala-Computing repo.
Mount points: `atlas/remote/mandala/`.
