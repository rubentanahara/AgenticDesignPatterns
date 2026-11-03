PYTHON ?= $(if $(wildcard $(HOME)/.venvs/adp/bin/python),$(HOME)/.venvs/adp/bin/python,python3)
DIR := $(firstword $(wildcard $(CH)-*))
SCRIPTS := $(notdir $(wildcard $(DIR)/*.py))
FILE ?= $(if $(word 2,$(SCRIPTS)),,$(SCRIPTS))

.PHONY: run
run:
	@test -n "$(CH)" || { echo "usage: make run CH=01 [FILE=script.py]"; exit 1; }
	@test -n "$(DIR)" || { echo "no chapter folder matches $(CH)-*"; exit 1; }
	@test -n "$(SCRIPTS)" || { echo "$(DIR) has no scripts"; exit 1; }
	@test -n "$(FILE)" || { echo "$(DIR) has several scripts, pick one with FILE=: $(SCRIPTS)"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) "$(DIR)/$(FILE)"
