#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the Django project directory (adjust path as needed)
# Uncomment and modify the next line if your manage.py is in a different directory
cd "/root/alxprodev/alx-backend-graphql_crm"

# Log file path
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Python command to execute in Django shell
PYTHON_COMMAND="
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

# Import your models (adjust import paths according to your app structure)
# Replace 'your_app' with your actual app name
try:
    from your_app.models import Customer, Order
except ImportError as e:
    print(f'Import error: {e}')
    print('Please update the import statement with your correct app name and model names')
    exit(1)

# Calculate the date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the past year
customers_to_delete = Customer.objects.filter(
    # Option 1: Customers with no orders at all
    order__isnull=True
).union(
    # Option 2: Customers with orders, but none in the past year
    Customer.objects.exclude(
        order__created_at__gte=one_year_ago
    ).exclude(
        order__isnull=True
    )
).distinct()

# Alternative query if you prefer a different approach:
# customers_to_delete = Customer.objects.exclude(
#     order__created_at__gte=one_year_ago
# ).distinct()

# Count customers before deletion
customer_count = customers_to_delete.count()

# Perform the deletion in a transaction
try:
    with transaction.atomic():
        deleted_count, _ = customers_to_delete.delete()
        print(f'Successfully deleted {customer_count} customers with no orders since {one_year_ago.strftime(\"%Y-%m-%d\")}')
        print(f'DELETED_COUNT:{customer_count}')
except Exception as e:
    print(f'Error during deletion: {e}')
    print('DELETED_COUNT:0')
"

echo "Starting customer cleanup process..."
echo "Timestamp: $TIMESTAMP"

# Execute the Python command in Django shell and capture output
OUTPUT=$(python3 manage.py shell -c "$PYTHON_COMMAND" 2>&1)
EXIT_CODE=$?

# Extract the deleted count from output
DELETED_COUNT=$(echo "$OUTPUT" | grep "DELETED_COUNT:" | cut -d':' -f2)

# If extraction failed, set to 0
if [ -z "$DELETED_COUNT" ]; then
    DELETED_COUNT=0
fi

# Create log entry
if [ $EXIT_CODE -eq 0 ]; then
    LOG_ENTRY="[$TIMESTAMP] Customer cleanup completed successfully. Deleted $DELETED_COUNT customers with no orders since $(date -d '1 year ago' '+%Y-%m-%d')"
    echo "✅ $LOG_ENTRY"
else
    LOG_ENTRY="[$TIMESTAMP] Customer cleanup failed with exit code $EXIT_CODE. Error: $OUTPUT"
    echo "❌ $LOG_ENTRY"
fi

# Append to log file
echo "$LOG_ENTRY" >> "$LOG_FILE"

# Display the output for debugging
echo ""
echo "Full output:"
echo "$OUTPUT"

echo ""
echo "Log entry written to: $LOG_FILE"

# Exit with the same code as the Django command
exit $EXIT_CODE