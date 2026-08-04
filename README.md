# typst-post

Post-compilation utilities for [Typst](https://typst.app) documents: booklet
imposition, page rotation, page reordering, and project packing.

Typst deliberately keeps its compiler focused on producing documents, so
workflow requests like rotating a single page
([typst#5559](https://github.com/typst/typst/issues/5559)), rearranging output
([typst#332](https://github.com/typst/typst/issues/332)), booklet printing
([typst#5092](https://github.com/typst/typst/issues/5092)), or bundling a
project with its assets ([typst#579](https://github.com/typst/typst/issues/579))
are closed as out of scope. typst-post picks up where the compiler stops. It
operates on the compiled PDF (or the source tree), never on your markup, and
every transformation is a pure vector operation — nothing is rasterized.

The PDF commands work on any PDF, not just Typst output.

## Installation

```
pipx install typst-post
```

or `pip install typst-post`. Requires Python 3.9+. The `pack` command
additionally needs the `typst` CLI on your PATH.

## Usage

### booklet

Impose pages as a 2-up saddle-stitch booklet: print the result double-sided
(flip on short edge), fold the stack in half, and it reads in order.

```
typst-post booklet thesis.pdf
typst-post booklet zine.pdf --sheet a4
typst-post booklet book.pdf --signature 16
```

By default each output spread is exactly twice the input page width, so an A5
document becomes A4 spreads with no scaling. `--sheet` scales and centers the
spreads onto a named size (a3, a4, a5, letter, legal) instead. `--signature`
splits the document into folded signatures of N pages (a multiple of 4) for
thicker, bound booklets.

### rotate

Rotate individual pages by multiples of 90 degrees.

```
typst-post rotate scans.pdf 2:180
typst-post rotate deck.pdf 5-8:90 12:180
typst-post rotate doc.pdf all:180
```

### reorder

Reorder, duplicate, or drop pages with a page list. Ranges may run backwards.

```
typst-post reorder doc.pdf 4,1,2,3
typst-post reorder doc.pdf 1-3,8-5      # keep 1-3, then 8..5 reversed
typst-post reorder doc.pdf 1,3,5,7      # drop the even pages
```

### pack

Zip a Typst project together with every file it actually depends on — images,
imported files, fonts loaded from the tree — ready to hand to a co-author or
print shop. The dependency list comes from the compiler itself
(`typst compile --deps`, falling back to `--make-deps` on older versions), so
nothing is guessed from the source text.

```
typst-post pack main.typ
typst-post pack main.typ -o handoff.zip --with-pdf
```

Files outside the project root (such as the package cache) are skipped, since
Typst restores packages on its own.

## Roadmap

- Creep compensation and inner margins for thick booklets
- n-up imposition beyond 2-up
- Watch hooks: re-run any of the above on `typst watch` recompiles
  ([typst#3362](https://github.com/typst/typst/issues/3362))

## License

MIT
