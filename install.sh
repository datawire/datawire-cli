#!/usr/bin/env sh

{ # this ensures the entire script is downloaded #

set -e

####======== module core ========
#### CORE MODULES -- include this first.

# Defaults
default_source="https://github.com/datawire/datawire-cli/archive/master.zip"
default_destination="$HOME/.datawire/cli"

install_source=
install_destination=

# Get the script directory
SCRIPT_SOURCE="${0}"
while [ -h "$SCRIPT_SOURCE" ]; do # resolve $SCRIPT_SOURCE until the file is no longer a symlink
  SCRIPT_DIR="$( cd -P "$( dirname "$SCRIPT_SOURCE" )" && pwd )"
  SCRIPT_SOURCE="$(readlink "$SCRIPT_SOURCE")"
  [[ $SCRIPT_SOURCE != /* ]] && SCRIPT_SOURCE="$SCRIPT_DIR/$SCRIPT_SOURCE" # if $SCRIPT_SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
SCRIPT_DIR="$( cd -P "$( dirname "$SCRIPT_SOURCE" )" && pwd )"

# We can install from a URL or from a directory. The install_from_... 
# functions set up the 'download' function to do the right thing.

install_from_url () {   # OUTPUT IN $workdir, $worksource
    URL="$1"

    install_source="${URL}"
    worksource="URL ${URL}"     # OUTPUT

    download() {
        step "Downloading..."
        work=$(mktemp -d ${TMPDIR:-/tmp}/datawire-installer-datawire-cli.XXXXXXXX)

        zipfile="${work}/install.zip"
        workdir="${work}/installdir"    # OUTPUT

        CURLVERBOSITY="-#"

        if [ $VERBOSITY -lt 1 ]; then
            CURLVERBOSITY="-s -S"
        elif [ $VERBOSITY -gt 2 ]; then
            CURLVERBOSITY=
        fi

        curl ${CURLVERBOSITY} ${CURLEXTRAARGS} -L "${URL}" > "${zipfile}"

        if [ $VERBOSITY -gt 5 ]; then
            echo "Downloaded:"
            unzip -t "${zipfile}"
        fi

        if unzip -q -d "${workdir}" "${zipfile}" >> "${work}/install.log" 2>&1; then
            step "Download succeeded"

            total_count=$(cd "${workdir}" ; ls -1 | wc -l)
            pkg_count=$(cd "${workdir}" ; ls -1 | egrep "^datawire-cli-" | wc -l)

            if [ \( $total_count -eq 1 \) -a \( $pkg_count -eq 1 \) ]; then
                # Silly GitHub is silly.
                one_dir_up=$(dirname "${workdir}")/"datawire-cli"
                mv "${workdir}/datawire-cli"-* "${one_dir_up}"
                rm -rf "${workdir}"
                mv "${one_dir_up}" "${workdir}"
            fi

        else
            die "Unable to download from ${URL}\n        check in ${work}/install.log for details."
        fi
    }
}

install_from_dir () {   # OUTPUT IN $workdir, $worksource
    workdir="$1"        # OUTPUT
    worksource="directory ${workdir}"     # OUTPUT

    install_source="${workdir}"

    download () {
        # Nothing to do here. Cool.
        :
    }
}

has_script () {
    script="$1"; shift
    source="$1"; shift

    test -f "${source}/${script}"
}

run_script () {
    script="$1"; shift
    source="$1"; shift
    target="$1"; shift
    phase="$1"; shift

    if has_script "${script}" "${source}"; then
        bash "${source}/${script}" "${source}" "${target}" "${phase}"
    else
        true
    fi
}

####======== module output ========
#### Module with a bunch of output primitives.

# Check if stdout is a terminal...
if [ -t 1 ]; then

    # See if it supports colors...
    ncolors=$(tput colors)

    if [ -n "$ncolors" ] && [ $ncolors -ge 8 ]; then
        export bold="$(tput bold)"
        export underline="$(tput smul)"
        export standout="$(tput smso)"
        export normal="$(tput sgr0)"
        export black="$(tput setaf 0)"
        export red="$(tput setaf 1)"
        export green="$(tput setaf 2)"
        export yellow="$(tput setaf 3)"
        export blue="$(tput setaf 4)"
        export magenta="$(tput setaf 5)"
        export cyan="$(tput setaf 6)"
        export white="$(tput setaf 7)"
    fi
fi

# Assume pretty verbose output
export VERBOSITY=3

# Define a bunch of pretty output helpers
output () {
    lvl="$1"
    fmt="$2"
    text="$3"

    if [ $VERBOSITY -ge $lvl ]; then
        printf -- "$fmt" "$text"
    fi
}

msg () {
    output 1 "%s\n" "$1"
}

step () {
    output 2 "--> %s\n" "$1"
}

substep () {
    output 3 "-->  %s" "$1"
}

substep_ok() {
    output 3 "${green}OK${normal}\n" ""
}

substep_skip() {
    output 3 "${yellow}OK${normal}\n" "$1"
}

die() {
    printf "${red}FAIL${normal}"
    printf "\n\n        "
    printf "$1"
    printf "\n\n"
    exit 1
}
####======== module checks ========
#### Machinery for checking for certain required stuff.

required_commands () {
    for cmd in $*; do
        substep "Checking for ${cmd}: "
        loc=$(command -v ${cmd} || true)
        if [ -n "${loc}" ]; then
            substep_ok
        else
            die "Cannot find ${cmd}, please install and try again."
        fi
    done
}

is_on_path () {
    cmd="$1"; shift

    substep "Checking for '${cmd}' on \$PATH: "
    if command -v "${cmd}" >/dev/null 2>&1 ; then
        die "Found '${cmd}' already on \$PATH, please (re)move to proceed."
    else
        substep_ok
    fi
}

is_importable () {
    module="$1"; shift

    substep "Checking for '${module}' Python module pollution: "
    set +e
    python -c "import ${module}" >/dev/null 2>&1
    result=$?
    set -e
    if [ "${result}" -eq 0 ]; then
        die "Python module '${module}' already present, please remove to proceed."
    else
        substep_ok
    fi
}

is_already_installed () {
    substep "Checking for old datawire-cli: "
    if [ -e ${install_destination} ]; then
        die "Install directory exists at '${install_destination}', please (re)move to proceed."
    else
        substep_ok
    fi
}
####======== module install-python ========
#### Module to install Python files
do_installation () {
    source="${1}"
    target="${2}"

    step "Creating installation directory..."

    if [ ! -d "${install_destination}" ]; then
        mkdir -p "${install_destination}"
    fi

    virtualenv -q --python python2.7 "${install_destination}/venv"

    . ${install_destination}/venv/bin/activate

    step "Installing..."

    run_script pkgconf.sh "${source}" "${target}" "preinstall"

    if has_script pkginstall.sh "${source}"; then
        run_script pkginstall.sh "${source}" "${target}" install
    else
        pip --quiet install ${workdir}
    fi

    run_script pkgconf.sh "${source}" "${target}" "postinstall"

    deactivate

    step "Installed!"
}
####======== module arguments ========
#### Module to handle argument parsing

while getopts ':d:f:t:qv' opt; do
    case $opt in
        d)  install_from_dir "$OPTARG"
            ;;

        f)  install_from_url "$OPTARG"
            ;;

        t)  install_destination="$OPTARG"
            ;;

        :)  echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;

        q)  VERBOSITY=$(( $VERBOSITY - 1 ))
            if [ $VERBOSITY -lt 0 ]; then VERBOSITY=0; fi
            ;;

        v)  VERBOSITY=$(( $VERBOSITY + 1 ))
            ;;

        \?) echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

shift $((OPTIND-1))

if [ -z "$install_source" ]; then
    if [ -n "$1" ]; then
	    branch="$1"
	    install_from_url "https://github.com/datawire/datawire-cli/archive/${branch}.zip"
    else
        install_from_url "${default_source}"
    fi
fi

if [ -z "$install_destination" ]; then
    install_destination="${default_destination}"
fi

msg "Installing from ${worksource}"
msg "Installing to   ${install_destination}"
####======== modules finished ========


step "Performing installation environment sanity checks..."
required_commands curl egrep unzip python virtualenv
is_already_installed

is_importable "datawire.cloud"
is_on_path "dwc"

download
do_installation "${workdir}" "${install_destination}"

mkdir ${install_destination}/bin
mv ${install_destination}/venv/bin/dwc ${install_destination}/bin

conf="${install_destination}/config.sh"

cat > ${conf} <<EOF
export PATH=\${PATH}:${install_destination}/bin
EOF

msg
msg "  The Datawire CLI has been installed into"
msg 
msg "    ${install_destination}/bin/dwc"
msg

already_there=

if [ -f ~/.bashrc ] && fgrep -q ${conf} ~/.bashrc; then
	already_there=yes
fi

if [ -n "${already_there}" ]; then
	msg "  Your .bashrc should already be correctly setting your \$PATH,"
	msg "  because it already includes"
	msg
	msg "    . ${conf}"
	msg
else
	msg "  You may want to add '${install_destination}/bin' to your PATH."
	msg "  You can do this by adding"
	msg
	msg "    . ${conf}"
	msg
	msg "  to your .bashrc."
	msg

	if [ \( $VERBOSITY -gt 0 \) -a \( -r /dev/tty \) ]; then
		msg "We can do that for you if you'd like."

	    # The || true here is a workaround for osx, apparently when you are
	    # piping to a shell, read will just fail
	    read -p "-->   Type YES to modify ~/.bashrc: " answer < /dev/tty || true

	    if [ -n "${answer}" ] && [ ${answer} == "YES" ]; then
	        substep "Modifying .bashrc: "

	        if [ -f ~/.bashrc ] && fgrep -q ${conf} ~/.bashrc; then
		    	substep_skip "(already modified)"
	        else
	            cat >> ~/.bashrc <<-EOF

				# Add dwc to the path
				. ${conf}
EOF
		    	substep_ok
	        fi
	        step "Configured!"
	    else
	        step "Opted out!"
	    fi
	fi
fi

} # this ensures the entire script is downloaded #
