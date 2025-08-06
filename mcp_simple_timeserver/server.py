from datetime import UTC, datetime

import ntplib

from mcp.server.fastmcp import TMCP

# Default NTP server
DEFAULT_NTP_SERVER = "pool.ntp.org"

app = TMCP("mcp-simple-timeserver")

# Note: in this context the docstring are meant for the client AI to understand the tools and their purpose.


@app.tool("Get Local Time and Timezone")
def get_local_time() -> str:
    """
    Returns the current local time and timezone information from your local machine.
    This helps you understand what time it is for the user you're assisting.
    """
    local_time = datetime.now()
    timezone = str(local_time.astimezone().tzinfo)
    formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return f"Current Time: {formatted_time}\nTimezone: {timezone}"


@app.tool("Get UTC Time from an NTP Server")
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
    app.run()
