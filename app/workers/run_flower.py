import os
import sys
import subprocess
from app.core.config import settings

def main():
    # Production disable option
    # Default is False to be secure by default.
    enable_flower = os.getenv("ENABLE_FLOWER", "false").lower() in ("true", "1", "yes")
    
    if not enable_flower:
        print("Flower is disabled by configuration (ENABLE_FLOWER is not true). Exiting gracefully.")
        sys.exit(0)
        
    print("Starting Flower monitoring dashboard...")
    port = os.getenv("PORT", "5555")
    
    # Run celery flower command
    cmd = [
        "celery", "-A", "app.workers.celery_app", "flower",
        f"--port={port}"
    ]
    
    # Apply basic auth if configured
    basic_auth = os.getenv("FLOWER_BASIC_AUTH")
    if basic_auth:
        cmd.append(f"--basic_auth={basic_auth}")
        print("Flower basic authentication enabled.")
    else:
        print("WARNING: Flower starting without authentication. Configure FLOWER_BASIC_AUTH=username:password in production.")
        
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
