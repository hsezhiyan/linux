#! /usr/bin/env python3

# Script to gracefully shut down all running virtual machines accessible to the 'virtsh' command.
# It was initially designed for QEMU/KVM machines, but might work with more hypervisors.

# The VMs are tried to be shut down by triggering a "power-button-pressed" event in each machine.
# Each guest OS is responsible to shut down when detecting one. By default, some systems may just show
# an user dialog prompt instead and do nothing. If configured, this script can turn them off forcibly.
# That would be similar to holding the power button or pulling the AC plug on a real machine.

# This script exits with code 0 when all VMs could be shut down or were forced off at timeout.
# If the 'virsh shutdown VM_NAME' command returned an error, this script will exit with error code 1.
# On timeout with KILL_ON_TIMEOUT set to False, the script will exit with error code 2.
# If KILL_ON_TIMEOUT is active and the timeout was reached, but one of the 'virsh destroy VM_NAME' commands
# returned an error, this script exits with error code 3.


import subprocess
import time
from optparse import OptionParser

# Function to get a list of running VM names:
def list_running_vms():
    as_string = subprocess.check_output(["virsh", "list", "--state-running", "--name"], universal_newlines=True).strip()
    return [] if not as_string else as_string.split("\n")

# Evaluate command-line arguments:
parser = OptionParser(version="%prog 1.0")
parser.add_option("-i", "--interval", type="float", dest="interval", default=1,
                  help="Interval to use for polling the VM state after sending the shutdown command. (default: %default)")
parser.add_option("-t", "--timeout", type="float", dest="timeout", default=30,
                  help="Time to wait for all VMs to shut down. (default: %default)")
parser.add_option("-k", "--kill-on-timeout", action="store_true", dest="kill", default=False,
                  help="Kill (power cut) all remaining VMs when the timeout is reached. "
                       "Otherwise exit with error code 1. (default: %default)")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                  help="Print verbose status output. (default: %default)")
parser.add_option("-z", "--zenity", action="store_true", dest="zenity", default=False,
                  help="Print progress lines for 'zenity --progress' GUI progress dialog. (default: %default)")
(options, args) = parser.parse_args()

# List all running VMs:
running_vms = list_running_vms()

# Print summary of what will happen:
print("Shutting down all running VMs (currently {}) within {} seconds. {} remaining VMs.".format(
       len(running_vms), options.timeout, "Kill all" if options.kill else "Do not kill any"))

# Send shutdown command ("power-button-pressed" event) to all running VMs:
any_errors = False
if options.zenity:
    print("# Sending shutdown signals...", flush=True)
for vm in running_vms:
    if options.verbose:
        ok = subprocess.call(["virsh", "shutdown", vm])
    else:
        ok = subprocess.call(["virsh", "shutdown", vm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ok != 0:
        print("Error trying to shut down VM '{}' (code {})!".format(vm, ok))
        any_errors = True

# Don't start waiting if there was any error sending the shutdown command, exit with error:
if any_errors:
    print("ERROR: could not successfully send all shutdown commands!")
    exit(3)

# Wait for all VMs to shut down, but at most MAX_WAIT seconds. Poll every INTERVAL seconds::
t0 = time.time()
while running_vms:
    num_of_vms = len(running_vms)
    t = time.time() - t0
    if options.zenity:
        print("# Waiting for {} VM{} to shut down... ({} seconds left)".format(
               num_of_vms, "" if num_of_vms == 1 else "s", int(options.timeout - t)), flush=True)
        print(int(100 * t/options.timeout) if t < options.timeout else 99, flush=True)
    if options.verbose or t > options.timeout:
        print("\n[{:5.1f}s] Still waiting for {} VMs to shut down:".format(t, num_of_vms))
        print(" > " + "\n > ".join(running_vms))
    if t > options.timeout:
        if options.kill:
            print("\nTimeout of {} seconds reached! Killing all remaining VMs now!".format(options.timeout))
            if options.zenity:
                print("# Timeout reached! Have to kill the remaining {}.".format(
                       "VM" if num_of_vms == 1 else "{} VMs".format(num_of_vms)), flush=True)
            for vm in running_vms:
                if options.verbose:
                    ok = subprocess.call(["virsh", "destroy", vm])
                else:
                    ok = subprocess.call(["virsh", "destroy", vm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if ok != 0:
                    if options.verbose:
                        print("Error trying to forcibly kill VM '{}' (code {})!".format(vm, ok))
                    any_errors = True
            if any_errors:
                print("ERROR: could not successfully send all destroy commands!")
                exit(3)
        else:
            print("ERROR: Timeout of {} seconds reached!".format(options.timeout))
            exit(1)
        break
    time.sleep(options.interval)
    running_vms = list_running_vms()

print("#" if options.zenity else "" + " All VMs were shut down successfully.", flush=True)
if options.zenity:
    print(100, flush=True)
exit(0)