from datetime import datetime, UTC
import ntplib
from fastmcp import FastMCP  # FastMCP 2.0 import

# Create the FastMCP app with web-specific settings
app = FastMCP(
    "mcp-simple-timeserver", 
    stateless_http=True,
    host="0.0.0.0",  # Listen on all interfaces inside the container
    port=8000,
    auth=None  # Explicitly disable authentication
)

DEFAULT_NTP_SERVER = 'pool.ntp.org'

@app.tool(
    annotations = {
        "title": "Get Local Time and Timezone for the Server Hosting this Tool",
        "readOnlyHint": True
    }
)
def get_server_time() -> str:
    """
    Returns the current local time and timezone from the server hosting this tool.
    Note: This is the server's time, which may be different from the user's local time.
    """
    local_time = datetime.now()
    timezone = str(local_time.astimezone().tzinfo)
    formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return f"Current Server Time: {formatted_time}\nTimezone: {timezone}"

@app.tool(
    annotations = {
        "title": "Get UTC Time from an NTP Server",
        "readOnlyHint": True
    }
)
def get_utc(server: str = DEFAULT_NTP_SERVER) -> str:
    """
    Returns accurate UTC time from an NTP server.
    This provides a universal time reference regardless of local timezone.
    
    :param server: NTP server address (default: pool.ntp.org)
    """
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request(server, version=3)
        utc_time = datetime.fromtimestamp(response.tx_time, tz=UTC)
        formatted_time = utc_time.strftime("%Y-%m-%d %H:%M:%S")
        return f"Current UTC Time from {server}: {formatted_time}"
    except ntplib.NTPException as e:
        return f"Error getting NTP time: {str(e)}" 
    

if __name__ == "__main__":
    # Run the server with streamable-http transport
    app.run(transport="streamable-http")