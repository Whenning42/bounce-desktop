set -euo pipefail

parse_args() {
    if [ "$#" -lt 5 ] || [ "$4" != "--" ]; then
        echo "Usage: $0 <handshake-file> <display-width> <display-height> -- <subcompositor-command> [args...]" >&2
        exit 1
    fi

    SUBCOMPOSITOR_HANDSHAKE_FILE=$1
    DISPLAY_WIDTH=$2
    DISPLAY_HEIGHT=$3
    shift 4
    SUBCOMPOSITOR_COMMAND=("$@")
}

if [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "Missing required environment variable: WAYLAND_DISPLAY" >&2
    exit 1
fi

parse_args "$@"

# Write display to handshake file for desktop to fetch.
echo "Starting Display $WAYLAND_DISPLAY"
echo "$WAYLAND_DISPLAY" > "$SUBCOMPOSITOR_HANDSHAKE_FILE"

# Fetch the wayland output name for this display and resize the output
# to the desired width and height.
OUT=$(WAYLAND_DISPLAY="${WAYLAND_DISPLAY}" wlr-randr | awk '/^[^ ]/ {print $1; exit}')
wlr-randr --output "$OUT" --custom-mode "${DISPLAY_WIDTH}x${DISPLAY_HEIGHT}@60Hz"

"${SUBCOMPOSITOR_COMMAND[@]}"
