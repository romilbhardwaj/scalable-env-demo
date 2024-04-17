import subprocess
import textwrap
import time
import uuid

import yaml
from fastapi import FastAPI
import sky

app = FastAPI()

CONTAINER_PORT = 8000
CONTAINER_IMAGE = 'us-central1-docker.pkg.dev/skypilot-375900/skypilotk8s/skypilot:20240321'

skypilot_yaml = textwrap.dedent(f"""
resources:
  cloud: kubernetes
  image_id: docker:{CONTAINER_IMAGE}
  cpus: 1+
  memory: 1+
  ports: {CONTAINER_PORT}

run: |
  python -m http.server {CONTAINER_PORT}
""")
skypilot_task = sky.Task.from_yaml_config(yaml.safe_load(skypilot_yaml))

skypilot_running_clusters = {}

@app.get("/create_container")
def create_container():
    # Generate a unique cluster name
    cluster_name = 'demo-' + str(uuid.uuid4().hex[:6])
    try:
        # Launch the skypilot task
        _, handle = sky.launch(task=skypilot_task,
                               cluster_name=cluster_name,
                               detach_run=True) # Detach so that the web server can run

        # Store the cluster name in the running clusters
        skypilot_running_clusters[cluster_name] = handle

        # Get endpoint of cluster. This will be a lot cleaner and done with python
        # after https://github.com/skypilot-org/skypilot/pull/3377
        cmd = f'SKYPILOT_DEBUG=0 sky status --endpoint {CONTAINER_PORT} {cluster_name}'
        # Run using subprocess while exit code is not 0
        while True:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                break  # Exit loop if command is successful
            time.sleep(1)
        # Parse the endpoint from stdout
        endpoint = stdout.decode().strip()
    except Exception as e:  # Kinda bad, but whatever
        return {"error": str(e)}
    return {"container_name": cluster_name, "endpoint": endpoint}

@app.get("/delete_container")
def delete_container(container_name: str):
    sky.down(cluster_name=container_name)
    return {"message": f"Container {container_name} deleted"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)