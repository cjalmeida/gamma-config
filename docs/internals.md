# Multiple dispatch

From the version `0.3.x` on, `gamma-config` was rewritten to use
[multiple dispatch](https://en.wikipedia.org/wiki/Multiple_dispatch) as core paradigm
instead of typical class based object orientation. All multiple dispatch code is
under the `gamma.dispatch` namespace and I might create a dedicated library in the
future.

## Rationale

The main reason was for me to learn more about the feasability of using multiple
dispatch in Python in a non-trivial project. I was inspired in how multiple dispatch
enabled a rich ecosystem of reusable components Julia language, in a very short time.

For the theorically inclined, multiple dispatch solves the
[expression problem](https://eli.thegreenplace.net/2016/the-expression-problem-and-its-solutions/)
in a very elegant way. In summary, the expression problem is a fundamental issue in
programming language design: how can you structure your application so that you can:

-   add new behavior (functions) to existing types
-   add new types that can be used with existing behavior
-   without changing original code
-   with no or minimal repetition

This is actually **a solved problem** for most languages, including Python, using a
variety of techniques, where multiple dispatch is one of them (and probably the most
elegant). But what sets Julia apart is that it's the only language where multiple
dispatch is the core paradigm. This means that **idiomatic Julia code is easily amenable
to extension** (and performant). In contrast in most languages you have be very explict
about extensibility, adding unwarranted complexity, something frowned upon by the
[You-Aint-Gonna-Need-It](https://martinfowler.com/bliki/Yagni.html) principle.

Interestingly, the impact of multiple dispatch on code reuse was an unplanned
side-effect. I recommend watching the following presentation by one of Julia creators:

<iframe width="560" height="315" src="https://www.youtube.com/embed/kc9HwsxE1OY"
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
allowfullscreen></iframe>

For a number of reasons, I don't think we should go full Julia (yet). But what if
idiomatic Python code had the same level of extensibility? Python is flexible enough
that we could "bend the rules" and, with some tooling, make multiple-dispatch a first
class citizen by convention. My (long shot) bet is that with a little
coordination, we could greatly improve code reuse across cases.

## Dispatch rules

Multiple dispatch works in a intuitive way for the large majority of the time. Since
there's no canonical set of rules, I followed to Julia docs and behavior on
[function](https://docs.julialang.org/en/v1/manual/functions)
and [methods](https://docs.julialang.org/en/v1/manual/methods). We also share the same
terminology of generic "functions" and associated "methods".

We mark a function as part of a multiple-dispatch group by annotation with `@dispatch`.
Two `@dispatch` annotated functions with the same name, in the same scope are
considered "one single function with two methods. All **POSITIONAL** and **POSITIONAL_OR_KEYWORD**
arguments are used for dispatching. Variadic positional arguments (eg. `_args`) and
keyworkd-only arguments (those after `_`or`\*args`) are not considered for dispatching.

Consider the example below:

```py
from gamma.dispatch import dispatch


@dispatch
def foo(**kwargs):
    return "fallback"

@dispatch
def foo(a):
    return "any"

@dispatch
def foo(a: int):
    return "int"

assert foo(100) == "int"
assert foo("a") == "any"
assert foo() == "fallback"
```

In regular Python dispatch, you can also call the function `foo` above as `foo(a=1)`.
Because we only dispatch on positional arguments, this would give the non-obvious
error of calling `foo(**kwargs)` passing `{'a': 1}` as keyword argument. To avoid the
confusion, we "reserve" positional argument names. Thus `foo(a=1)` will raise an error.

Note you can still use keyword-only arguments, but you should separate them from
positional arguments using the `*` separator.

```py
@dispatch
def foo(a: int, *, c=1):
    return "kw"

assert(1, c=2) == "kw"
```

### Parametric dispatch

_TODO_

### Missing features

-   Type/length constraints for variadic arguments

### Other considerations

-   Multiple dispatch is slower compared to simple function or wrapped `__call__`
    dispatch. It's still pretty fast for most purposes, just avoid using it in "hot"
    loops.

-   Tie-breaking is done via the output of `type.mro()` (Method Resolution Order). We
    still support dynamic subclass definition via `__subclasshook__`, but limited
    tie-breaking since we can't determine the proper type hierarchy.

-   Multiple inheritance may also introduce ambiguities or non-obvious behavior to
    dispatch tie-breaking.
