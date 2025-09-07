from datetime import datetime
import os

def log_crm_heartbeat():
    """
    Logs a heartbeat message to verify CRM is alive.
    Optionally queries GraphQL hello field to verify endpoint responsiveness.
    """
    # Format timestamp as DD/MM/YYYY-HH:MM:SS
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_file = '/tmp/crm_heartbeat_log.txt'
    
    # Basic heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"
    
    # Optional: Check GraphQL endpoint responsiveness
    graphql_status = ""
    try:
        from gql import gql, Client
        from gql.transport.aiohttp import AIOHTTPTransport
        
        # Set up GraphQL client
        transport = AIOHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Simple hello query
        query = gql("""
        query {
            hello
        }
        """)
        
        result = client.execute(query)
        hello_response = result.get('hello', 'No response')
        graphql_status = f" - GraphQL endpoint responsive: {hello_response}"
        
    except Exception as e:
        graphql_status = f" - GraphQL endpoint error: {str(e)}"
    
    # Complete log message
    full_message = heartbeat_message + graphql_status
    
    # Append to log file
    try:
        with open(log_file, 'a') as f:
            f.write(full_message + '\n')
        print(f"Heartbeat logged: {full_message}")
    except Exception as e:
        print(f"Error writing heartbeat log: {str(e)}")