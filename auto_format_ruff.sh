uvx ruff check --fix
uvx ruff format
if ! git diff --quiet; then
    git add .
    git commit -m "[ruff] auto format"
fi
