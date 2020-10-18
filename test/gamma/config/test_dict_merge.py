from gamma.config.yaml_merge import merge
from ruamel.yaml import YAML


def test_merge():

    # test simple
    target = {"foo": "bar"}
    patch = {"foo": "baz"}
    merge(target, patch)
    assert target["foo"] == "baz"

    # test dict merging
    target = {"foo": {"a": 1, "b": 2}}
    patch = {"foo": {"b": 20, "c": 30}}
    merge(target, patch)
    assert target == {"foo": {"a": 1, "b": 20, "c": 30}}

    # assert list merging
    target = {"foo": [1, 2]}
    patch = {"foo": [2, 3]}
    merge(target, patch)
    assert target == {"foo": [1, 2, 3]}

    # test type replacement (1)
    target = {"foo": [1, 2]}
    patch = {"foo": {"b": 20, "c": 30}}
    merge(target, patch)
    assert target == {"foo": {"b": 20, "c": 30}}

    # test type replacement (1)
    target = {"foo": {"a": 1, "b": 2}}
    patch = {"foo": [2, 3]}
    merge(target, patch)
    assert target == {"foo": [2, 3]}


def test_hints():
    yaml = YAML()

    # assert replace hint on inline lists
    target = {"foo": [1, 2]}
    patch = yaml.load(
        """
        foo: [2, 3] # @hint: merge_replace
        """
    )
    merge(target, patch)
    assert target == {"foo": [2, 3]}

    # assert replace hint on expanded lists
    target = {"foo": [1, 2]}
    patch = yaml.load(
        """
        foo: # @hint: merge_replace
          - 2
          - 3
        """
    )
    merge(target, patch)
    assert target == {"foo": [2, 3]}

    # test dict merging inline map
    target = {"foo": {"a": 1, "b": 2}}
    patch = yaml.load(
        """
        foo: {"b": 20, "c": 30} # @hint: merge_replace
        """
    )
    merge(target, patch)
    assert target == {"foo": {"b": 20, "c": 30}}

    # test dict merging expanded map
    target = {"foo": {"a": 1, "b": 2}}
    patch = yaml.load(
        """
        foo:  # @hint: merge_replace
          b: 20
          c: 30
        """
    )
    merge(target, patch)
    assert target == {"foo": {"b": 20, "c": 30}}

    # test nested maps with tags
    target = {"foo": {"args": [1]}}
    patch = yaml.load(
        """
        foo: !bar # @hint: merge_replace
          args: [2]
        """
    )
    merge(target, patch)
    assert target == {"foo": {"args": [2]}}

    # test some hint syntax variants - 1
    target = {"foo": {"a": 1, "b": 2}}
    patch = yaml.load(
        """
        foo: {"b": 20, "c": 30} #@hint: merge_replace
        """
    )
    merge(target, patch)
    assert target == {"foo": {"b": 20, "c": 30}}

    # test some hint syntax variants - 2
    target = {"foo": {"a": 1, "b": 2}}
    patch = yaml.load(
        """
        foo: {"b": 20, "c": 30} #  @hint:   merge_replace
        """
    )
    merge(target, patch)
    assert target == {"foo": {"b": 20, "c": 30}}
