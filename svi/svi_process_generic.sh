#!/bin/bash

# Version information
VERSION="1.0.0"
MODULE_NAME="SVI Processing"

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
PYTHON_SCRIPT="$(dirname "$0")/svi_process_generic.py"

# Pass all arguments to the python script
# We do NOT activate environment here - user must have dependencies installed
python3 "$PYTHON_SCRIPT" "$@"
