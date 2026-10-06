"""Run the packaged PWA. No Node installation or build is needed to try it."""
import argparse
import os
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GrimeQuest locally")
    parser.add_argument("--host", default="127.0.0.1", help="Default is local-only. Public access requires an HTTPS reverse proxy.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    uvicorn.run("server.app:app", host=args.host, port=args.port, workers=1, proxy_headers=False,
                access_log=False, timeout_keep_alive=5, limit_concurrency=24)
