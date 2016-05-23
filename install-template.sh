#!/usr/bin/env sh

{ # this ensures the entire script is downloaded #

set -e

{{{MODULES}}}

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
