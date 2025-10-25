#!/bin/bash
# U/N Algebra Phase 3 Test Execution Script
# Runs comprehensive 102k+ test suite

set -e

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="../../validation/phase_3_results"
LOG_FILE="${RESULTS_DIR}/test_run_${TIMESTAMP}.log"
SUMMARY_FILE="${RESULTS_DIR}/test_summary_${TIMESTAMP}.txt"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}U/N Algebra Phase 3 Validation${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Test Suite:${NC} 102,000+ cases"
echo -e "${YELLOW}Categories:${NC} Unit, Fuzz, Projection, Interval, Scenario, Operators"
echo -e "${YELLOW}Output:${NC} ${LOG_FILE}\n"

# Create results directory if it doesn't exist
mkdir -p "${RESULTS_DIR}"

# Navigate to Python source
cd ../../src/python

# Run test suite
echo -e "${GREEN}Starting test execution...${NC}\n"
python3 -m tests.test_suite 2>&1 | tee "${LOG_FILE}"

# Extract summary
echo -e "\n${GREEN}Extracting summary...${NC}"
grep -A 20 "TEST SUMMARY" "${LOG_FILE}" > "${SUMMARY_FILE}" || echo "Summary extraction failed"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Test execution complete${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Log file:${NC} ${LOG_FILE}"
echo -e "${YELLOW}Summary:${NC} ${SUMMARY_FILE}\n"

# Show summary
cat "${SUMMARY_FILE}"
