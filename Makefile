SHELL := /bin/bash
PACKAGE_NAME = reports
ifneq ($(wildcard billing.cfg),)
	CFG = billing.cfg
else
	CFG = buildout.cfg
endif
default: install;

install:
	@test -d "bin" || virtualenv . --no-site-packages --clear
	@test -x "bin/buildout" || bin/pip install -r requirements.txt
	bin/buildout -N -c $(CFG)

help:
	@echo "Makefile for $(PACKAGE_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make    install the package in a virtual environment'
	@echo

clean:
	@rm -rf eggs/ develop-eggs/ bin/ etc/ lib/ parts/ include/ logs/