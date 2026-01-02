#!/bin/bash

# Version information
VERSION="1.0.0"
MODULE_NAME="COI Processing"

# Version display function
show_version() {
    echo "$MODULE_NAME Framework v$VERSION"
    exit 0
}

# Check for version argument
if [[ "$1" == "--version" || "$1" == "-V" ]]; then
    show_version
fi

# Locate the python script
PYTHON_SCRIPT="$(dirname "$0")/coi_process_generic.py"

# Pass all arguments to the python script
python3 "$PYTHON_SCRIPT" "$@"
