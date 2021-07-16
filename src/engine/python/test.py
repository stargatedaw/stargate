"""
    Test the experimental Python C extension version of the engine
    Run `make pymod` first, and run this script from the same directory
    as the *.so file
"""

import os
import stargateengine

def callback(k, v):
    print(f"{k}: {v}")

stargateengine.init(callback)

project_dir = os.path.join(
    os.path.expanduser('~'),
    "stargate",
    "projects",
    "default-project",
)

stargateengine.start(project_dir)

print("Stopping...")
stargateengine.stop()

print("Stopped")
