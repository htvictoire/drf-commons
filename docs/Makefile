SPHINXOPTS ?=
SPHINXBUILD ?= sphinx-build
SOURCEDIR = .
BUILDDIR = _build

.PHONY: html clean

html:
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

clean:
	rm -rf "$(BUILDDIR)"
