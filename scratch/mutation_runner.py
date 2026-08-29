"""
NATIVE WINDOWS AST MUTATION TESTING RUNNER FOR APP/PARSER.PY AND APP/HELPERS.PY
Generates true syntactic mutations (conditional flips, constant changes, boundary mutations)
against the real application source files, runs the authentic property test suite, and calculates
the exact Mutation Kill Score (killed / total * 100).
"""

import ast
import os
import sys
import subprocess
import shutil

TARGET_FILES = [
    os.path.abspath(r"C:\Users\humza\suprajit_v2\app\parser.py"),
    os.path.abspath(r"C:\Users\humza\suprajit_v2\app\helpers.py")
]

class ASTMutationTransformer(ast.NodeTransformer):
    def __init__(self, target_mutation_index):
        self.target_mutation_index = target_mutation_index
        self.current_mutation_index = 0
        self.applied_description = None

    def visit_Compare(self, node):
        self.generic_visit(node)
        # Flip comparisons: == -> !=, < -> <=, in -> not in
        for i, op in enumerate(node.ops):
            self.current_mutation_index += 1
            if self.current_mutation_index == self.target_mutation_index:
                if isinstance(op, ast.Eq):
                    node.ops[i] = ast.NotEq()
                    self.applied_description = f"Line {node.lineno}: mutated '==' to '!='"
                elif isinstance(op, ast.NotEq):
                    node.ops[i] = ast.Eq()
                    self.applied_description = f"Line {node.lineno}: mutated '!=' to '=='"
                elif isinstance(op, ast.Lt):
                    node.ops[i] = ast.Gt()
                    self.applied_description = f"Line {node.lineno}: mutated '<' to '>'"
                elif isinstance(op, ast.In):
                    node.ops[i] = ast.NotIn()
                    self.applied_description = f"Line {node.lineno}: mutated 'in' to 'not in'"
                elif isinstance(op, ast.NotIn):
                    node.ops[i] = ast.In()
                    self.applied_description = f"Line {node.lineno}: mutated 'not in' to 'in'"
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            self.current_mutation_index += 1
            if self.current_mutation_index == self.target_mutation_index:
                node.value = not node.value
                self.applied_description = f"Line {node.lineno}: mutated bool constant to {node.value}"
        elif isinstance(node.value, int) and node.value in (0, 1, 4, 12, 60):
            self.current_mutation_index += 1
            if self.current_mutation_index == self.target_mutation_index:
                node.value = node.value + 1
                self.applied_description = f"Line {node.lineno}: mutated integer {node.value - 1} to {node.value}"
        return node


def count_available_mutations(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    transformer = ASTMutationTransformer(target_mutation_index=-1)
    transformer.visit(tree)
    return transformer.current_mutation_index


def apply_mutation_to_file(file_path, mutation_index):
    with open(file_path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    transformer = ASTMutationTransformer(target_mutation_index=mutation_index)
    mutated_tree = transformer.visit(tree)
    ast.fix_missing_locations(mutated_tree)
    mutated_src = ast.unparse(mutated_tree)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(mutated_src)
    return transformer.applied_description


def run_mutation_audit():
    total_mutants = 0
    killed_mutants = 0
    survived_mutants = []

    print("=" * 70)
    print("STARTING AST MUTATION AUDIT ON REAL APPLICATION CODE")
    print("=" * 70)

    for file_path in TARGET_FILES:
        backup_path = file_path + ".bak"
        shutil.copyfile(file_path, backup_path)
        
        num_mutations = count_available_mutations(file_path)
        print(f"Target: {os.path.basename(file_path)} -> {num_mutations} potential mutation points found.")

        for mut_idx in range(1, num_mutations + 1):
            total_mutants += 1
            desc = apply_mutation_to_file(file_path, mut_idx)
            
            # Run authentic property test suite against the mutated code
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "-c", "pytest.ini", "tests/test_property_filename_parser.py", "tests/test_property_security_helpers.py", "-q"],
                capture_output=True,
                text=True
            )

            # If tests fail, mutant was KILLED (success). If tests pass, mutant SURVIVED (missed bug).
            if res.returncode != 0:
                killed_mutants += 1
                status = "KILLED"
            else:
                survived_mutants.append((os.path.basename(file_path), desc))
                status = "SURVIVED"

            print(f"  [Mutant #{total_mutants:02d}] {status} -> {desc}")

            # Restore original clean code
            shutil.copyfile(backup_path, file_path)

        if os.path.exists(backup_path):
            os.remove(backup_path)

    kill_score = (killed_mutants / total_mutants * 100) if total_mutants > 0 else 0.0

    print("=" * 70)
    print(f"MUTATION TESTING RESULTS:")
    print(f"Total Mutants Evaluated : {total_mutants}")
    print(f"Mutants Killed          : {killed_mutants}")
    print(f"Mutants Survived        : {len(survived_mutants)}")
    print(f"Mutation Kill Score     : {kill_score:.2f}%")
    print("=" * 70)

    if survived_mutants:
        print("\nSURVIVED MUTATIONS (Areas to harden):")
        for f, d in survived_mutants:
            print(f"  - {f}: {d}")

if __name__ == "__main__":
    run_mutation_audit()
