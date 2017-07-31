%{?scl:%scl_package clang}
%{!?scl:%global pkg_name %{name}}
%global devtoolset_name devtoolset-7

%global clang_tools_binaries \
	%{_bindir}/clang-apply-replacements \
	%{_bindir}/clang-change-namespace \
	%{_bindir}/clang-include-fixer \
	%{_bindir}/clang-query \
	%{_bindir}/clang-reorder-fields \
	%{_bindir}/clang-rename \
	%{_bindir}/clang-tidy

%global clang_binaries \
	%{_bindir}/clang \
	%{_bindir}/clang++ \
	%{_bindir}/clang-4.0 \
	%{_bindir}/clang-check \
	%{_bindir}/clang-cl \
	%{_bindir}/clang-cpp \
	%{_bindir}/clang-format \
	%{_bindir}/clang-import-test \
	%{_bindir}/clang-offload-bundler

Name:		%{?scl:%scl_prefix}clang
Version:	4.0.1
Release:	1%{?dist}
Summary:	A C language family front-end for LLVM

License:	NCSA
URL:		http://llvm.org
Source0:	http://llvm.org/releases/%{version}/cfe-%{version}.src.tar.xz
Source1:	http://llvm.org/releases/%{version}/clang-tools-extra-%{version}.src.tar.xz

Patch1:		0001-Driver-Update-devtoolset-usage-for-RHEL.patch
Patch2:		0001-Driver-Don-t-mix-system-tools-with-devtoolset-tools-.patch
Patch3:		0001-Driver-Add-gcc-search-path-for-RHEL-devtoolset-7.patch

BuildRequires:	%{?scl:%scl_prefix}cmake
BuildRequires:	%{?scl:%scl_prefix}llvm-devel = %{version}
BuildRequires:	libxml2-devel
BuildRequires:  %{?scl:%scl_prefix}llvm-static = %{version}
#BuildRequires:  perl-generators
BuildRequires:  ncurses-devel

Requires:	%{?scl:%scl_prefix}%{pkg_name}-libs%{?_isa} = %{version}-%{release}

%description
clang: noun
    1. A loud, resonant, metallic sound.
    2. The strident call of a crane or goose.
    3. C-language family front-end toolkit.

The goal of the Clang project is to create a new C, C++, Objective C
and Objective C++ front-end for the LLVM compiler. Its tools are built
as libraries and designed to be loosely-coupled and extensible.

%package libs
Summary: Runtime library for clang
Requires: %{?scl_prefix}compiler-rt%{?_isa} >= %{version}

# libomp does not support s390x.
%ifnarch s390x
Requires: %{?scl_prefix}libomp%{?_isa} >= %{version}
%endif

# clang requires gcc, clang++ requires libstdc++-devel
# - https://bugzilla.redhat.com/show_bug.cgi?id=1021645
# - https://bugzilla.redhat.com/show_bug.cgi?id=1158594

# Making these BuildRequires because they are needed by tests
BuildRequires:	%{?scl:%{devtoolset_name}-}libstdc++-devel
BuildRequires:	%{?scl:%{devtoolset_name}-}gcc-c++
Requires:	%{?scl:%{devtoolset_name}-}libstdc++-devel
Requires:	%{?scl:%{devtoolset_name}-}gcc-c++


%description libs
Runtime library for clang.

%package devel
Summary: Development header files for clang.
Requires: %{?scl:%scl_prefix}%{pkg_name}%{?_isa} = %{version}-%{release}

%description devel
Development header files for clang.

%package analyzer
Summary:	A source code analysis framework
License:	NCSA and MIT
BuildArch:	noarch
Requires:	%{?scl:%scl_prefix}%{pkg_name} = %{version}-%{release}
# not picked up automatically since files are currently not installed in
# standard Python hierarchies yet
Requires:	python

%description analyzer
The Clang Static Analyzer consists of both a source code analysis
framework and a standalone tool that finds bugs in C and Objective-C
programs. The standalone tool is invoked from the command-line, and is
intended to run in tandem with a build of a project or code base.

%package tools-extra
Summary: Extra tools for clang
Requires: %{?scl:%scl_prefix}llvm-libs%{?_isa} = %{version}
Requires: %{?scl:%scl_prefix}clang-libs%{?_isa} = %{version}-%{release}

%description tools-extra
A set of extra tools built using Clang's tooling API.

%prep
%setup -T -q -b 1 -n clang-tools-extra-%{version}.src

%setup -q -n cfe-%{version}.src
%patch1 -p1 -b .driver-devtoolset6
%patch2 -p1 -b .driver-devtoolset6-bin
%patch3 -p1 -b .driver-devtoolset7

mv ../clang-tools-extra-%{version}.src tools/extra

%build
mkdir -p _build
cd _build

# Use the scl-provided cmake instead of /usr/bin/cmake
%global __cmake %{_bindir}/cmake

%cmake .. \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DLLVM_CONFIG:FILEPATH=%{_bindir}/llvm-config \
	\
	-DCLANG_ENABLE_ARCMT:BOOL=ON \
	-DCLANG_ENABLE_STATIC_ANALYZER:BOOL=ON \
	-DCLANG_INCLUDE_DOCS:BOOL=ON \
	-DCLANG_INCLUDE_TESTS:BOOL=OFF \
	-DCLANG_PLUGIN_SUPPORT:BOOL=ON \
	-DENABLE_LINKER_BUILD_ID:BOOL=ON \
	-DLLVM_ENABLE_EH=ON \
	-DLLVM_ENABLE_RTTI=ON \
	\
	-DCLANG_BUILD_EXAMPLES:BOOL=OFF \
%if 0%{?__isa_bits} == 64
        -DLLVM_LIBDIR_SUFFIX=64 \
%else
        -DLLVM_LIBDIR_SUFFIX= \
%endif
	-DLIB_SUFFIX=

make %{?_smp_mflags}

%install
cd _build
make install DESTDIR=%{buildroot}

# remove git integration
rm -vf %{buildroot}%{_bindir}/git-clang-format
# remove editor integrations (bbedit, sublime, emacs, vim)
rm -vf %{buildroot}%{_datadir}/clang/clang-format-bbedit.applescript
rm -vf %{buildroot}%{_datadir}/clang/clang-format-sublime.py*
rm -vf %{buildroot}%{_datadir}/clang/clang-format.el
rm -vf %{buildroot}%{_datadir}/clang/clang-format.py*
# clang-tools-extra
rm -vf %{buildroot}%{_datadir}/clang/clang-include-fixer.py
rm -vf %{buildroot}%{_datadir}/clang/clang-tidy-diff.py
rm -vf %{buildroot}%{_datadir}/clang/run-clang-tidy.py
rm -vf %{buildroot}%{_datadir}/clang/run-find-all-symbols.py
rm -vf %{buildroot}%{_datadir}/clang/clang-include-fixer.el
rm -vf %{buildroot}%{_datadir}/clang/clang-rename.el
rm -vf %{buildroot}%{_datadir}/clang/clang-rename.py
# remove diff reformatter
rm -vf %{buildroot}%{_datadir}/clang/clang-format-diff.py*

%check
# requires lit.py from LLVM utilities
#cd _build
#make check-all

%{?scl:scl enable %scl - << \EOF}
set -ex
./_build/bin/clang -v 2>&1 | grep  'Selected GCC installation: /opt/rh/%{devtoolset_name}/root/usr/lib/gcc/'

# Make sure clang is using ld from devtoolset
test `echo 'int main(){}' | ./_build/bin/clang -### -x cl - 2>&1 | grep 'bin/ld' | cut -d ' ' -f 2 | sed 's/"//g'` -ef /opt/rh/%{devtoolset_name}/root/bin/ld
%{?scl:EOF}

%files
%{_libdir}/clang/
%{clang_binaries}
%{_bindir}/c-index-test

%files libs
%{_libdir}/*.so.*
%{_libdir}/*.so

%files devel
%{_includedir}/clang/
%{_includedir}/clang-c/
%{_libdir}/cmake/
%dir %{_datadir}/clang/

%files analyzer
%{_bindir}/scan-view
%{_bindir}/scan-build
%{_bindir}/scan-build
%{_libexecdir}/ccc-analyzer
%{_libexecdir}/c++-analyzer
%{_datadir}/scan-view/
%{_datadir}/scan-build/
%{_mandir}/man1/scan-build.1.*

%files tools-extra
%{clang_tools_binaries}
%{_bindir}/find-all-symbols
%{_bindir}/modularize

%changelog
* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-1
- 4.0.1 Release.

* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-15
- Fix Requires for clang-tools-extra

* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com - 4.0.0-14
- Fix Requires for clang-tools-extra

* Tue Jun 20 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-13
- Drop libomp dependency on s390x

* Thu Jun 15 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-12
- Use libstdc++ from devtoolset-7

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-11
- Fix libomp requires

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-10
- Build for llvm-toolset-7 rename

* Tue May 30 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-9
- Use ld from devtoolset in clang toolchain

* Mon May 29 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-8
- Add dependency on libopenmp

* Thu May 25 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-7
- Fix check for gcc install

* Wed May 24 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-6
- Add devtoolset-6 dependency for newer libstdc++

* Fri May 12 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-5
- Add dependency on compiler-rt

* Tue May 02 2017 Tom Stellard <tstellar@redhat.com>
- Fix dependencies with scl

* Mon May 01 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-4
- Build with llvm-toolset-4

* Mon Mar 27 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-3
- Enable eh/rtti, which are required by lldb.

* Fri Mar 24 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-2
- Fix clang-tools-extra build
- Fix install

* Thu Mar 23 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-1
- clang 4.0.0 final release

* Mon Mar 20 2017 David Goerger <david.goerger@yale.edu> - 3.9.1-3
- add clang-tools-extra rhbz#1328091

* Thu Mar 16 2017 Tom Stellard <tstellar@redhat.com> - 3.9.1-2
- Enable build-id by default rhbz#1432403

* Thu Mar 02 2017 Dave Airlie <airlied@redhat.com> - 3.9.1-1
- clang 3.9.1 final release

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 14 2016 Nathaniel McCallum <npmccallum@redhat.com> - 3.9.0-3
- Add Requires: compiler-rt to clang-libs.
- Without this, compiling with certain CFLAGS breaks.

* Tue Nov  1 2016 Peter Robinson <pbrobinson@fedoraproject.org> 3.9.0-2
- Rebuild for new arches

* Fri Oct 14 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- clang 3.9.0 final release

* Fri Jul 01 2016 Stephan Bergmann <sbergman@redhat.com> - 3.8.0-2
- Resolves: rhbz#1282645 add GCC abi_tag support

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- clang 3.8.0 final release

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.4
- clang 3.8.0rc3

* Wed Feb 24 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.3
- package all libs into clang-libs.

* Wed Feb 24 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.2
- enable dynamic linking of clang against llvm

* Thu Feb 18 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.1
- clang 3.8.0rc2

* Fri Feb 12 2016 Dave Airlie <airlied@redhat.com> 3.7.1-4
- rebuild against latest llvm packages
- add BuildRequires llvm-static

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 28 2016 Dave Airlie <airlied@redhat.com> 3.7.1-2
- just accept clang includes moving to /usr/lib64, upstream don't let much else happen

* Thu Jan 28 2016 Dave Airlie <airlied@redhat.com> 3.7.1-1
- initial build in Fedora.

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
