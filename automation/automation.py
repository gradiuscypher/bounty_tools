import json
import random
import digitalocean
import multiprocessing
import time
import logging.config
from recon import reconng
from connectivity import do_wrapper
from database import elastic_bounty_tools

# Configure Logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger('bounty_tools')


def add_args(parser):
    parser.add_argument("--bulkrecon", help="Run recon on a bulk set of hosts in a JSON file", action="store_true")
    parser.add_argument("--hostjson", help="JSON file containing list of workspaces and targets")
    parser.add_argument("--distribute", help="Number of scanners to distribute scans across")


def parse_args(args, config):
    if args.bulkrecon and args.hostjson is not None:
        with open(args.hostjson) as json_data:
            json_hosts = json.load(json_data)
        bulk_recon(args, config, json_hosts)


def bulk_recon(args, config, json_hosts):
    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    if args.distribute is not None:
        # Get enough droplets so that we can distribute between scanners, do this in multiprocess
        droplets = manager.get_all_droplets()
        required_droplets = int(args.distribute)

        if len(droplets) < required_droplets:
            more_droplets = required_droplets - len(droplets)
            logger.debug("Creating {} more droplets".format(more_droplets))

            jobs = []
            for x in range(0, more_droplets):
                mp_worker = multiprocessing.Process(target=do_wrapper.create_vm, args=(config,))
                jobs.append(mp_worker)
                logger.debug("Making a droplet...")
                mp_worker.start()

            # Iterate over the job list and wait for each process to be complete
            while len(jobs) > 0:
                jobs = [job for job in jobs if job.is_alive()]
                print("Waiting for {} jobs, sleeping...".format(len(jobs)))
                time.sleep(5)

        bounty_droplets = manager.get_all_droplets(tag_name="bounty")
        total_targets = len(json_hosts)

        # Build work queue
        work_queue = multiprocessing.Queue()
        for target in json_hosts:
            work_queue.put((target, json_hosts[target]))

        # Build workers
        droplet_workers = []
        for droplet in bounty_droplets:
            p = multiprocessing.Process(target=droplet_worker, args=(args, config, droplet, work_queue,))
            droplet_workers.append(p)

        # Distribute scans and launch, then collect results and run enrichment, do this in multiprocess
        for worker in droplet_workers:
            worker.start()

        # Wait for all workers
        while not work_queue.empty():
            print("Still working ... ", end="\r")
            time.sleep(1)

    else:
        if args.droplet is None:
            args.droplet = do_wrapper.create_vm(config)

        for target in json_hosts:
            args.workspace = target
            args.domains = json_hosts[target]
            reconng.parse_args(args, config)
            elastic_bounty_tools.parse_args(args, config)


def droplet_worker(args, config, droplet, queue):
    while not queue.empty():
        # Get target info from queue
        print(droplet.id, "Grabbing work...")
        target = queue.get()
        args.workspace = target[0]
        args.domains = target[1]
        args.droplet = droplet

        # Run recon and import to elastic
        reconng.parse_args(args, config)
    else:
        print("queue is empty")
