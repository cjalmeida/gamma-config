from gamma.config import RootConfig


def test_anchors():
    test = """
foo: &foo
  sub1: 10
  sub2: 20

bar:
  <<: *foo
  sub2: 22
  sub3: 33
  subx: *foo

val1: &val1 100

l1:
    - *val1
    - 200
    - 300
"""

    cfg = RootConfig(None, test)

    assert cfg["l1"] == [100, 200, 300]

    assert cfg["bar"]["sub1"] == 10
    assert cfg["bar"]["sub2"] == 22
    assert cfg["bar"]["sub3"] == 33
    assert cfg["bar"]["subx"] == {"sub1": 10, "sub2": 20}

    assert cfg["foo"]["sub1"] == 10
    assert cfg["foo"]["sub2"] == 20
