#
# Project Wok
#
# Copyright IBM Corp, 2013-2016
#
# Code derived from Project Kimchi
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

SUBDIRS = src ui docs contrib po tests

man_MANS = docs/wokd.8

AUTOMAKE_OPTIONS = foreign

ACLOCAL_AMFLAGS = --install -I m4

EXTRA_DIST = \
	config.rpath \
	autogen.sh \
	COPYING.ASL2 \
	COPYING.LGPL \
	CONTRIBUTE.md \
	VERSION \
	build-aux/pkg-version \
	$(NULL)


PEP8_BLACKLIST = *src/wok/plugins,*src/wok/config.py,*src/wok/i18n.py,*tests/test_config.py

SKIP_PYFLAKES_ERR = "\./src/wok/websocket\.py"

I18N_FILES = src/wok/plugins/*/i18n.py \
	src/wok/i18n.py \
	$(NULL)

check-local:
	PYTHONPATH=src contrib/check_i18n.py $(I18N_FILES)
	@if [ -d '.git' ]; then                                        	\
		find . -path './.git' -prune -o                        	   	\
			-name '*.py' -o -name '*.py.in'  |             			\
			xargs $(PYFLAKES) |                            			\
			while read LINE; do echo "$$LINE"; false; done 			\
	else                                                           	\
		find . -name '*.py' -o -name '*.py.in'  |              		\
			xargs $(PYFLAKES) |                            			\
			while read LINE; do echo "$$LINE"; false; done 			\
	fi
	$(PEP8) --version
	$(PEP8) --filename '*.py,*.py.in' --exclude="$(PEP8_BLACKLIST)" .
	/bin/bash check_ui_code_errors.sh
	@if $(GIT) rev-parse &> /dev/null ; then                        \
		echo "Whitespace verification ...";                         \
		git grep --cached -Il '' |                                  \
			grep -v '^ui/css/src/vendor/' | xargs egrep '.* +$$' 	\
			&& echo "ERROR: Whitespaces found" || echo "Ok";     	\
		echo "Check IBM license header and copyright date ..." ;    \
		/bin/bash check-IBM-license-header.sh ;						\
		fi;
		@if [ -f $(RPMLINT) ]; then 								\
			./check_spec_errors.sh; 								\
		fi;

# Link built mo files in the source tree to enable use of translations from
# within the source tree
all-local:
	while read L && test -n "$$L"; do                  \
		dir=mo/$$L/LC_MESSAGES ;                       \
		$(MKDIR_P) $$dir ;                             \
		ln -sf ../../../po/$$L.gmo $$dir/wok.mo ;   \
	done < po/LINGUAS

#
# Packaging helpers
#

install-deb: install
	cp -R $(top_srcdir)/contrib/DEBIAN $(DESTDIR)/
	@if test -d "$(systemdsystemunitdir)" ; then \
		$(MKDIR_P) $(DESTDIR)/$(systemdsystemunitdir); \
		cp -R contrib/wokd.service.fedora \
			$(DESTDIR)/$(systemdsystemunitdir)/wokd.service; \
	else \
		$(MKDIR_P) $(DESTDIR)/etc/init; \
		cp -R $(top_srcdir)/contrib/wokd-upstart.conf.debian \
			$(DESTDIR)/etc/init/wokd.conf; \
	fi
	$(MKDIR_P) $(DESTDIR)/$(localstatedir)/lib/wok/


deb: contrib/make-deb.sh
	$(top_srcdir)/contrib/make-deb.sh

wok.spec: contrib/wok.spec.fedora contrib/wok.spec.suse
	@if test -e /etc/redhat-release; then                   \
		ln -sf contrib/wok.spec.fedora $@ ;              \
        elif test -e /etc/system-release; then			\
		ln -sf contrib/wok.spec.fedora $@ ;		\
	elif test -e /etc/SuSE-release; then                    \
		ln -sf contrib/wok.spec.suse $@ ;                \
	else                                                    \
		echo "Unable to select a spec file for RPM build" ; \
		/bin/false ;                                        \
	fi

rpm: dist wok.spec
	$(MKDIR_P) rpm/BUILD rpm/RPMS rpm/SOURCES rpm/SPECS rpm/SRPMS
	cp $(top_srcdir)/wok.spec rpm/SPECS/wok.spec
	cp $(DIST_ARCHIVES) rpm/SOURCES
	rpmbuild -ba --define "_topdir `pwd`/rpm" rpm/SPECS/wok.spec

fedora-rpm: dist contrib/wok.spec.fedora
	ln -sf contrib/wok.spec.fedora wok.spec
	$(MAKE) rpm

suse-rpm: dist contrib/wok.spec.suse
	ln -sf contrib/wok.spec.suse wok.spec
	$(MAKE) rpm

ChangeLog:
	@if $(GIT) rev-parse &> /dev/null ; then                     \
		$(top_srcdir)/build-aux/genChangelog --release > $@; \
	fi

install-data-local:
	@if test -d "$(systemdsystemunitdir)" ; then \
		mkdir -p $(DESTDIR)/$(systemdsystemunitdir); \
		$(INSTALL_DATA) contrib/wokd.service.fedora $(DESTDIR)/$(systemdsystemunitdir)/wokd.service; \
	else \
		mkdir -p $(DESTDIR)/etc/init.d/; \
		$(INSTALL_DATA) contrib/wokd.sysvinit $(DESTDIR)/etc/init.d/wokd; \
		chmod +x $(DESTDIR)/etc/init.d/wokd; \
	fi; \
	if test -d /usr/lib/firewalld/services/; then \
		mkdir -p $(DESTDIR)/usr/lib/firewalld/services/; \
		$(INSTALL_DATA) src/firewalld.xml $(DESTDIR)/usr/lib/firewalld/services/wokd.xml; \
	fi; \
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/
	mkdir -p $(DESTDIR)/$(localstatedir)/log/wok/
	touch $(DESTDIR)/$(localstatedir)/log/wok/wok-access.log
	touch $(DESTDIR)/$(localstatedir)/log/wok/wok-error.log
	mkdir -p $(DESTDIR)/etc/wok/
	$(INSTALL_DATA) src/dhparams.pem $(DESTDIR)/etc/wok/dhparams.pem
	touch $(DESTDIR)/etc/nginx/conf.d/wok.conf
	mkdir -p $(DESTDIR)/etc/logrotate.d/
	$(INSTALL_DATA) $(top_srcdir)/src/wok.logrotate $(DESTDIR)/etc/logrotate.d/wokd

uninstall-local:
	@if test -f $(systemdsystemunitdir)/wokd.service; then \
		$(RM) $(DESTDIR)/$(systemdsystemunitdir)/wokd.service; \
	elif test -f /etc/init.d/wokd; then \
		$(RM) $(DESTDIR)/etc/init.d/wokd; \
		$(RM) $(DESTDIR)/etc/init/wok.conf; \
	fi; \
	if test -d /usr/lib/firewalld/services/; then \
		$(RM) $(DESTDIR)/usr/lib/firewalld/services/wokd.xml; \
	fi; \
	$(RM) -rf $(DESTDIR)/$(localstatedir)/lib/wok
	$(RM) -rf $(DESTDIR)/$(localstatedir)/log/wok
	$(RM) -rf $(DESTDIR)/etc/wok
	$(RM) $(DESTDIR)/etc/nginx/conf.d/wok.conf
	$(RM) $(DESTDIR)/etc/logrotate.d/wokd

VERSION:
	@if $(GIT) rev-parse &> /dev/null ; then              \
		git describe --abbrev=0 --always > $@;        \
	fi

.PHONY: deb install-deb rpm fedora-rpm suse-rpm VERSION


clean-local:
	rm -rf mo rpm

CLEANFILES = wok.spec `find "$(top_srcdir)" -type f -name "*.pyc" -print`
