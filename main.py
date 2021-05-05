
import argparse
import hashlib
import json
import traceback
from typing import Callable, Dict

import click
from kubernetes import client, config, watch

GOOGLE_DOMAINS_API = "https://domains.google.com/nic/update"


def update_ddns():
    pass


def on_event(event: Dict):
    # TODO: Put UNKNOWN
    typ = event['type']
    ingress: client.NetworkingV1beta1Ingress = event['object']
    if typ == 'ADDED' or typ == 'MODIFIED':
        name = ingress.metadata.name
        if (lb := ingress.status.load_balancer) and (igs := lb.ingress) and igs[0] and (ip := igs[0].ip):
            update_ddns(name, ip)
    elif typ == 'DELETED':
        # Ignore
        pass
    else:
        print('UNKNOWN type')
        print(event)


@click.command(context_settings={'auto_envvar_prefix': 'K8S-INGRESS-DDNS'})
@click.option('--ddns-username', type=str, required=True, show_envvar=True)
@click.option('--ddns-password', type=str, required=True, show_envvar=True)
@click.option('--namespace', type=str, default="default", show_envvar=True)
def main(
    ddns_username: str, ddns_password: str, namespace: str,
):
    config.load_kube_config()

    v1 = client.NetworkingV1beta1Api()
    w = watch.Watch()
    # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.10/#watch-list-65
    for event in w.stream(v1.list_namespaced_ingress, namespace=namespace):
        try:
            on_event(event)
        except Exception:
            traceback.print_exc()
            print(event)

    w.stop()
