#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

def main():
    # GraphQL endpoint
    endpoint = "http://localhost:8000/graphql"
    
    # Log file path
    log_file = "/tmp/order_reminders_log.txt"
    
    # Calculate date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Set up GraphQL client
        transport = AIOHTTPTransport(url=endpoint)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # GraphQL query for orders within the last 7 days
        query = gql("""
        query GetRecentOrders($dateFrom: Date!) {
            orders(orderDate_Gte: $dateFrom) {
                id
                orderDate
                customer {
                    email
                }
            }
        }
        """)
        
        # Execute the query
        variables = {"dateFrom": seven_days_ago}
        result = client.execute(query, variable_values=variables)
        
        # Process the results
        orders = result.get('orders', [])
        
        # Open log file for appending
        with open(log_file, 'a') as f:
            f.write(f"\n[{current_timestamp}] Order reminders batch started\n")
            
            if orders:
                for order in orders:
                    order_id = order.get('id')
                    customer_email = order.get('customer', {}).get('email', 'N/A')
                    order_date = order.get('orderDate')
                    
                    # Log entry for each order
                    log_entry = f"[{current_timestamp}] Order ID: {order_id}, Customer Email: {customer_email}, Order Date: {order_date}"
                    f.write(log_entry + "\n")
                    
                f.write(f"[{current_timestamp}] Order reminders batch completed. Processed {len(orders)} orders\n")
            else:
                f.write(f"[{current_timestamp}] No orders found in the last 7 days\n")
        
        print("Order reminders processed!")
        
    except Exception as e:
        # Log any errors
        error_message = f"[{current_timestamp}] ERROR: {str(e)}"
        with open(log_file, 'a') as f:
            f.write(error_message + "\n")
        
        print(f"Error processing order reminders: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()