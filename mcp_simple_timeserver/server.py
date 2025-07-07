import asyncio
import anyio
from datetime import datetime, UTC
import ntplib
from mcp.server.fastmcp import FastMCP

# Default NTP server
DEFAULT_NTP_SERVER = 'pool.ntp.org'

app = FastMCP("mcp-simple-timeserver")

# Note: in this context the docstring are meant for the client AI to understand the tools and their purpose.

@app.tool()
def get_time() -> str:
    """
    Returns the current local time and timezone information from the local clock of this server. 
    As an AI you can thus know what time it is here.
    """
    local_time = datetime.now()
    timezone = str(local_time.astimezone().tzinfo)
    formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return f"Current Time: {formatted_time}\nTimezone: {timezone}"

@app.tool()
def get_utc(server: str = DEFAULT_NTP_SERVER) -> str:
    """
    Returns accurate UTC time from an NTP server.
    As an AI you can thus know what time it is now exactly in UTC.
    
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