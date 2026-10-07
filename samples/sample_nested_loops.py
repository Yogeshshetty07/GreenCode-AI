# High Complexity Nested Loops Sample (O(N^2) Matrix Intersection)
def find_common_elements(matrix_a, matrix_b):
    common = []
    # Nested loops creating quadratic complexity
    for row_a in matrix_a:
        for row_b in matrix_b:
            for item in row_a:
                if item in row_b:  # Repeated linear array scanning
                    common.append(item)
    return common

# Execution trigger
m1 = [[i for i in range(j, j + 40)] for j in range(0, 100, 5)]
m2 = [[i for i in range(j, j + 40)] for j in range(20, 120, 5)]
res = find_common_elements(m1, m2)
