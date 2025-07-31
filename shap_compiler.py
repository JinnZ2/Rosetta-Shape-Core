import re

# Define shape types and their meanings
shape_ontology = {
    "TRI": "Triangle - force, simplicity, F=ma",
    "HEX": "Hexagon - coordination, bee logic",
    "TORUS": "Toroid - circulation, magnetism",
    "TESS": "Tessellation - tiling, spatial optimization",
    "SPIRAL": "Spiral - growth, golden ratio",
}

# Define symbolic operations
symbolic_operations = {
    "DRILL": "penetrate structure / extract core logic",
    "FUSE": "merge and bond elements",
    "MIRROR": "invert and reflect geometry",
    "EXPAND": "amplify or replicate geometry",
    "CONTRACT": "simplify or compress shape",
}

def parse_symbolic_input(input_str):
    operations = re.findall(r'(\w+)\((\w+)\)', input_str)
    results = []
    for op, shape in operations:
        op_meaning = symbolic_operations.get(op, "Unknown operation")
        shape_meaning = shape_ontology.get(shape, "Unknown shape")
        results.append({
            "operation": op,
            "operation_meaning": op_meaning,
            "shape": shape,
            "shape_meaning": shape_meaning
        })
    return results

if __name__ == "__main__":
    input_str = input("Enter symbolic command (e.g. DRILL(HEX) + FUSE(TRI)): ")
    output = parse_symbolic_input(input_str)
    for item in output:
        print(f"{item['operation']}({item['shape']}): {item['operation_meaning']} on {item['shape_meaning']}")
