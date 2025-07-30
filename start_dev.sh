#!/bin/bash

# Get absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
    ln -s "$PROJECT_ROOT/githooks/pre-commit" "$PROJECT_ROOT/.git/hooks/pre-commit"
fi

STEPS_TO_INCLUDE=(project custom test_suite)

INCLUDES=""
for step in "${STEPS_TO_INCLUDE[@]}"; do
    INCLUDES="$INCLUDES --include-steps-root $PROJECT_ROOT/bundled_steps/$step"
done

# cd website && npm run test:[all,integration,unit]
cd "$PROJECT_ROOT/website" && nohup npm run dev &
cd "$PROJECT_ROOT" && uv run main.py $INCLUDES
