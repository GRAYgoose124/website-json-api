#!/bin/bash

if [ ! -f .git/hooks/pre-commit ]; then
    ln -s .githooks/pre-commit .git/hooks/pre-commit
fi

STEPS_TO_INCLUDE=(project custom test_suite)

INCLUDES=""
for step in "${STEPS_TO_INCLUDE[@]}"; do
    INCLUDES="$INCLUDES --include-steps-root ./bundled_steps/$step"
done

# cd website && npm run test:[all,integration,unit]
cd website && nohup npm run dev &
cd .. && uv run main.py $INCLUDES

