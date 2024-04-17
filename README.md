# scalable-env-demo
An example using SkyPilot to scale environments for agents.

## Setup
1. Install the SkyPilot nightly release
```console
pip install "skypilot-nightly[aws,gcp,kubernetes]"
```
2. Setup your infra/cloud accounts where you want to run the environments.
   * If using clouds - https://skypilot.readthedocs.io/en/latest/getting-started/installation.html#cloud-account-setup
   * If using Kubernetes see section below on creating k8s cluster. Then see https://skypilot.readthedocs.io/en/latest/getting-started/installation.html#kubernetes
3. Verify with `sky check`.

### [Optional] Create a Kubernetes cluster
If you want to use Kubernetes, you can create a GKE Kubernetes cluster with the following command:
```console
PROJECT_ID=$(gcloud config get-value project)
CLUSTER_NAME=mycluster
NUM_NODES=3
INSTANCE_TYPE=n1-standard-8
gcloud beta container --project "${PROJECT_ID}" clusters create "${CLUSTER_NAME}" --zone "us-central1-c" --no-enable-basic-auth --cluster-version "1.27.10-gke.1055000" --release-channel "regular" --machine-type "${INSTANCE_TYPE}" --image-type "COS_CONTAINERD" --disk-type "pd-balanced" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --num-nodes "${NUM_NODES}" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-ip-alias --network "projects/${PROJECT_ID}/global/networks/default" --subnetwork "projects/${PROJECT_ID}/regions/us-central1/subnetworks/default" --no-enable-intra-node-visibility --default-max-pods-per-node "110" --security-posture=standard --workload-vulnerability-scanning=disabled --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --enable-managed-prometheus --enable-shielded-nodes --node-locations "us-central1-c"
```
Or optionally use the web console.

You can also run a Kubernetes cluster locally for debugging with:
```console
sky local up
```

This will run a Kubernetes cluster on your local machine.

Remember to install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/).

## Running the example
`main.py` is a server that manages containers for agents. 

It defines a `skypilot_yaml` which specifies the resources and the cloud each container will run with.

It exposes two endpoints:
* `/create_container` - Creates a new container for an agent. This will invoke SkyPilot to launch the container and return the container's IP that can be accessed from anywhere.
* `/delete_container` - Deletes a container for an agent. This will invoke SkyPilot to delete the container (and its VM, if not running on k8s).

```console
python main.py
```

## Example output
After running the server, you can create a container by running:
```console
$ curl localhost:9000/create_container
# Takes some time. See server logs for progress.
{"container_name":"demo-40aeda","endpoint":"34.134.174.186:8000"}
```

You can then access the container at the returned endpoint. Your agent can use this endpoint to run its queries:
```console
$ curl 34.134.174.186:8000
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /</title>
</head>
<body>
<h1>Directory listing for /</h1>
<hr>
<ul>
</ul>
<hr>
</body>
</html>
```

You can delete the container by running:
```console
$ curl 'localhost:9000/delete_container?container_name=demo-40aeda'
{"message":"Container demo-40aeda deleted"}
```

### Notes
* When running on k8s, we can speed up container start by pre-fetching container images.
* Probably more optimizations to share containers if the application allows so.