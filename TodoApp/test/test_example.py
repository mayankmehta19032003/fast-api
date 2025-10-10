def test_equal_or_not_equal():
    assert 3 == 3
    assert 3 != 2

def test_is_instace():
    assert isinstance("this is string", str)
    assert not isinstance("10", int)

def test_boolean():
    validate = True
    assert validate is True
    assert ("hellw" == "world") is False

def test_type():
    assert type(3) is int
    assert type("hii") is not int

def test_greater_or_less_than():
    assert 5 > 3
    assert 3 < 5
   
def test_list():
    num_list = [1, 2, 3, 4, 5]
    any_list = [False,False]
    assert 1 in num_list
    assert 7 not in num_list
    assert all(num_list)
    assert not any(any_list)