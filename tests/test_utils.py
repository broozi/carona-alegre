from controllers.utils import is_valid_cpf, normalize_plate, only_digits


def test_only_digits():
    assert only_digits("(28) 99999-0000") == "28999990000"


def test_cpf_validation():
    assert is_valid_cpf("529.982.247-25")
    assert not is_valid_cpf("111.111.111-11")


def test_plate_normalization():
    assert normalize_plate("abc-1d23") == "ABC1D23"
