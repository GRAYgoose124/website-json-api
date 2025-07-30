#!
STEPS_TO_INCLUDE=(project custom test_suite)

INCLUDES=""
for step in "${STEPS_TO_INCLUDE[@]}"; do
    INCLUDES="$INCLUDES --include-steps-root ./bundled_steps/$step"
done

# cd website && npm test -- src/tests/api-integration.test.js
cd website && nohup npm run dev &
cd .. && uv run main.py $INCLUDES

