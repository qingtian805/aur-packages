#!/bin/bash

if [ -d ~/.config/QQ/versions ]; then
	find ~/.config/QQ/versions -name sharp-lib -type d -exec rm -r {} \; 2>/dev/null
	find ~/.config/QQ/versions -name libssh2.so.1 -type f -exec rm {} \; 2>/dev/null
fi

if [ -d ~/.config/QQ/crash_files ] && [ ! -L ~/.config/QQ/crash_files ]; then
	rm -rf ~/.config/QQ/crash_files/*
fi

XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-~/.config}

if [[ -f "${XDG_CONFIG_HOME}/qq-flags.conf" ]]; then
	mapfile -t QQ_USER_FLAGS <<<"$(grep -v '^#' "${XDG_CONFIG_HOME}/qq-flags.conf")"
	echo "User flags:" "${QQ_USER_FLAGS[@]}"
fi

exec /opt/QQ/qq "${QQ_USER_FLAGS[@]}" "$@"
