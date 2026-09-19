from kernellum.k2.protocol import reference_gemm


def test_reference_gemm_known_case():
    a = [[1, 2, 3], [4, 5, 6]]
    b = [[7, 8], [9, 10], [11, 12]]
    assert reference_gemm(a, b) == [[58, 64], [139, 154]]


def test_reference_gemm_signed_values():
    a = [[-1, 2], [3, -4]]
    b = [[5, -6], [7, 8]]
    assert reference_gemm(a, b) == [[9, 22], [-13, -50]]
