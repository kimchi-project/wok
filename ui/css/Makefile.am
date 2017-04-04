#
# Project Wok
#
# Copyright IBM Corp, 2013-2017
#
# Code derived from Project Kimchi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SUBDIRS = fontawesome

EXTRA_DIST = theme-default

cssdir = $(datadir)/wok/ui/css
dist_css_DATA = $(wildcard *.css)

wok: src/wok.scss src/modules/*.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< wok.css

bootstrap: src/bootstrap.custom.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< bootstrap.custom.css

user-log: src/user-log.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< user-log.css

settings: src/settings.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< settings.css

bootstrap-select: src/bootstrap-select.custom.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< bootstrap-select.custom.css

datatables: src/datatables.bootstrap.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< datatables.bootstrap.css

css: wok bootstrap bootstrap-select user-log settings  datatables

theme-default.min.css: theme-default/*.css
	cat $^ > $@

CLEANFILES = theme-default.min.css
