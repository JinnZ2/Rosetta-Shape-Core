import math
import random

# === Base classes for energy teachers ===
class Teacher:
    def __init__(self, name):
        self.name = name

    def influence(self, environment):
        """Return a list of energy behaviors or patterns"""
        return []

class AnimalTeacher(Teacher):
    def influence(self, environment):
        # Example: swarming, bursts, oscillations
        return [
            {"pattern": "swarm", "effect": random.uniform(0.5, 1.0)},
            {"pattern": "burst", "effect": random.uniform(0.2, 0.7)}
        ]

class PlantTeacher(Teacher):
    def influence(self, environment):
        # Fractals, branching, tension
        return [
            {"pattern": "fractal_surface", "effect": random.uniform(0.3, 0.9)},
            {"pattern": "branch_absorption", "effect": random.uniform(0.1, 0.6)}
        ]

class CrystalTeacher(Teacher):
    def influence(self, environment):
        # Resonance, lattice vibration
        return [
            {"pattern": "lattice_resonance", "effect": random.uniform(0.4, 1.0)},
            {"pattern": "phase_transition", "effect": random.uniform(0.2, 0.8)}
        ]

class PhysicsTeacher(Teacher):
    def influence(self, environment):
        # Waves, vortices, torsion
        return [
            {"pattern": "harmonic_wave", "effect": random.uniform(0.3, 1.0)},
            {"pattern": "vortex_flow", "effect": random.uniform(0.2, 0.9)}
        ]

# === Environment / Simulation Space ===
class EnergyPlayground:
    def __init__(self):
        self.teachers = []
        self.patterns = []

    def add_teacher(self, teacher):
        self.teachers.append(teacher)

    def run_step(self):
        self.patterns = []
        for t in self.teachers:
            self.patterns.extend(t.influence(self))
        # Optional: combine, mutate, or interact patterns
        self._interact_patterns()

    def _interact_patterns(self):
        # Simple interaction: sum effects of overlapping patterns
        combined = {}
        for p in self.patterns:
            key = p["pattern"]
            combined[key] = combined.get(key, 0) + p["effect"]
        # Normalize effects
        self.patterns = [{"pattern": k, "effect": min(v, 1.0)} for k, v in combined.items()]

    def report(self):
        print("Current energy patterns:")
        for p in self.patterns:
            print(f" - {p['pattern']}: {p['effect']:.2f}")

# === Example usage ===
playground = EnergyPlayground()
playground.add_teacher(AnimalTeacher("Hummingbirds"))
playground.add_teacher(PlantTeacher("Leaves"))
playground.add_teacher(CrystalTeacher("Quartz"))
playground.add_teacher(PhysicsTeacher("Harmonics"))

for step in range(5):
    print(f"\n--- Step {step + 1} ---")
    playground.run_step()
    playground.report()
