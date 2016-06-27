
TOP_DIR		= .

DOC_DIR		=	$(TOP_DIR)/doc
SOURCE_DIR	=	$(TOP_DIR)/fabtotum
LOCALE_DIR	= 	$(TOP_DIR)/locale

SPHINX_ARGS = --force --module-first --separate

.PHONY: sphinx

help:
	@echo "apidocs	- Generate API documentation."
	
apidocs:
	sphinx-apidoc $(SPHINX_ARGS) -o $(DOC_DIR)/source $(SOURCE_DIR)

locale:
