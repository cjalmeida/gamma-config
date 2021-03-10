# gamma-config internals

!>This section is intended only for people that want to contribute, extend or just learn
more about gamma-config.

## Multiple dispatch

From the version `0.3.x` on, `gamma-config` was rewritten to use
[multiple dispatch](https://en.wikipedia.org/wiki/Multiple_dispatch) as core paradigm
instead of typical class based object orientation. The approach leverages mostly the
work in https://github.com/coady/multimethod library to provide support for
**multimethods**.

The main reason was for me to learn more about the feasability of using multiple
dispatch in Python, in a non-trivial project. I was inspired in how multiple dispatch
enabled a rich ecosystem of reusable components Julia language in a very short time.

For the theorically inclined, multiple dispatch solves the
[expression problem](https://eli.thegreenplace.net/2016/the-expression-problem-and-its-solutions/)
in a very elegant way. In summary, the expression problem is a fundamental issue in
programming language design: how can you structure your application so that you can:

- add new behavior (functions) to existing types
- add new types that can be used with existing behavior
- without changing original code
- with no or minimal repetition

This is actually **a solved problem** for most languages, including Python, using a
variety of techniques, where multiple dispatch is one of them (and probably the most
elegant). But what sets Julia apart is that it's the only language where multiple
dispatch is the core paradigm. This means that **idiomatic Julia code is easily amenable
to extension** (and performant). In contrast in most languages you have be very explict
about extensibility, adding unwarranted complexity, something frowned upon by the
[You-Aint-Gonna-Need-It](https://martinfowler.com/bliki/Yagni.html) principle.

Interestingly, the impact of multiple dispatch on code reuse was an unplanned
side-effect. I recommend watching the following presentation by one of Julia creators:

<iframe width="560" height="315" src="https://www.youtube.com/embed/kc9HwsxE1OY" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## So what?!

Every year we write from scratch literally millions of lines of code solving similar
but not quite the same problems. Our level of code reuse is very low. As a consulting
company, we're doomed to work on a multitude of different environments. Creating a
*one-size-fits-all* framework that can handle even a small subset of scenarios is a
massive investment.

In fact, I argue that in the pressure of case work, it would be *detrimental
to the project* to actually create flexible, extensible code. You're just adding extra
complexity with a dubious immediate value. And the reason is that even good, idiomatic
Python (functional or OO) code is not naturally extensible due to the *expression
problem* stated above.

For a number of reasons, I don't think we should go full Julia (yet). But what if
idiomatic Python code had the same level of extensibility? Python is flexible enough
that we could "bend the rules" and make multiple-dispatch the core paradigm simply by
stylistic convention. My (long-shot) bet is that with point investments and a little
coordination, we could greatly improve code reuse across cases.

