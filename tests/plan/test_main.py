from app.main import add

def test_add():
    somma = add(a=2,b=3)
    assert somma == 5