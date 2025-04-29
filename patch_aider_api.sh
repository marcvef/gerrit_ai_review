#!/bin/bash

# Detect the active virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    # User is in an active virtual environment
    VENV_PATH="$VIRTUAL_ENV"
    echo "Using active virtual environment at: $VENV_PATH"
else
    # No active virtual environment, try to detect common names
    for venv_dir in "venv" ".venv" "env" ".env"; do
        if [ -d "$venv_dir" ]; then
            VENV_PATH="$(pwd)/$venv_dir"
            echo "Found virtual environment at: $VENV_PATH"
            break
        fi
    done

    if [ -z "$VENV_PATH" ]; then
        echo "Error: No virtual environment found. Please activate your virtual environment first."
        exit 1
    fi
fi

# Find the aider module in the virtual environment
if [ -d "$VENV_PATH/lib/python"* ]; then
    # Standard structure with lib/pythonX.Y
    PYTHON_DIR=$(find "$VENV_PATH/lib" -maxdepth 1 -type d -name "python*" | head -n 1)
    if [ -z "$PYTHON_DIR" ]; then
        echo "Error: Could not find Python directory in virtual environment."
        exit 1
    fi
    IO_FILE="$PYTHON_DIR/site-packages/aider/io.py"
elif [ -d "$VENV_PATH/Lib/site-packages" ]; then
    # Windows structure
    IO_FILE="$VENV_PATH/Lib/site-packages/aider/io.py"
else
    echo "Error: Could not locate site-packages directory in virtual environment."
    exit 1
fi

# Check if the file exists
if [ ! -f "$IO_FILE" ]; then
    echo "Error: $IO_FILE not found. Make sure Aider is installed in the virtual environment."
    exit 1
fi

# Find the line number of the confirm_ask method
CONFIRM_ASK_LINE=$(grep -n "def confirm_ask" "$IO_FILE" | cut -d':' -f1)
if [ -z "$CONFIRM_ASK_LINE" ]; then
    echo "Error: Could not find 'confirm_ask' method in $IO_FILE"
    exit 1
fi

# Find the line with the closing parenthesis and colon after the method definition
CLOSING_PAREN_LINE=$(grep -n -A 10 "def confirm_ask" "$IO_FILE" | grep -n "):" | head -n 1 | cut -d':' -f1)
if [ -z "$CLOSING_PAREN_LINE" ]; then
    echo "Error: Could not find closing parenthesis of confirm_ask method in $IO_FILE"
    exit 1
fi

# Calculate the actual line number in the file
CLOSING_PAREN_LINE=$((CONFIRM_ASK_LINE + CLOSING_PAREN_LINE - 1))

# Check if the line already exists after the closing parenthesis
if grep -A 1 "):" "$IO_FILE" | grep -q "return False"; then
    # Check if it's properly formatted - exact match with 8 spaces
    if grep -A 1 "):" "$IO_FILE" | grep -q "^        return False$"; then
        echo "The 'return False' line already exists with proper indentation."
        exit 0
    else
        echo "The 'return False' line exists but is not properly formatted. Will fix it."
        # We'll continue and fix the formatting
    fi
fi

# Line number where we want to add the return False (after the closing parenthesis)
LINE_NUM=$((CLOSING_PAREN_LINE + 1))

# Create a backup of the original file
cp "$IO_FILE" "${IO_FILE}.bak"
echo "Created backup at ${IO_FILE}.bak"

# Check if we need to fix existing line or add a new one
if grep -A 1 "):" "$IO_FILE" | grep -q "return False" && ! grep -A 1 "):" "$IO_FILE" | grep -q "^        return False$"; then
    echo "Fixing formatting of existing 'return False' line"

    # Create a temporary file
    TMP_FILE=$(mktemp)

    # Use awk to replace the line with proper indentation
    awk '{
        if ($0 ~ /return False/) {
            print "        return False"
        } else {
            print $0
        }
    }' "$IO_FILE" > "$TMP_FILE"

    # Replace the original file with our modified version
    cp "$TMP_FILE" "$IO_FILE"
    rm "$TMP_FILE"
else
    # Add the return False line with proper indentation
    echo "Adding 'return False' line after confirm_ask method definition (line $LINE_NUM)"

    # Create a temporary file
    TMP_FILE=$(mktemp)

    # Process the file: copy lines 1 to LINE_NUM-1, add our line, then copy the rest
    head -n $((LINE_NUM-1)) "$IO_FILE" > "$TMP_FILE"
    echo "        return False" >> "$TMP_FILE"
    tail -n +$LINE_NUM "$IO_FILE" >> "$TMP_FILE"

    # Replace the original file with our modified version
    cp "$TMP_FILE" "$IO_FILE"
    rm "$TMP_FILE"
fi

echo "Successfully added 'return False' with proper indentation to $IO_FILE"
