from langchain_mcp_adapters.client import MultiServerMCPClient  
from pathlib import Path
import sys
from dotenv import load_dotenv

load_dotenv()
SERVER = str(Path(__file__).resolve().parent / "mcp_server.py")

client = MultiServerMCPClient(
        {
            "reservation_saver": {
                "transport":"stdio",
                "command": sys.executable,
                "args": [SERVER],
            }
            })
