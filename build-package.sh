#!/bin/sh
set -eu

lang="${1:-}"

case "$lang" in
    ru|uk)
        ;;
    *)
        echo "Usage: $0 (ru|uk)" >&2
        exit 2
        ;;
esac

package_dir="pymorphy3-dicts-$lang"

if [ ! -d "$package_dir" ]; then
    echo "$package_dir does not exist." >&2
    echo "Generate it first with: python update.py $lang all" >&2
    exit 1
fi

cd "$package_dir"
python -m build .
