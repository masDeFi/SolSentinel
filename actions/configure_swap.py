import subprocess
import logging
import os
import sys

# Setup logging to file for tracking swap configuration actions
LOG_FILE = "swap_setup.log"
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def turn_swap_off():
    """
    Turn swap off using swapoff -a and return a result dict.
    Logs the attempt and result for auditing and debugging purposes.
    """
    result = {"name": "Swap Off", "status": "", "message": ""}
    logging.info("Attempting to turn swap off with 'swapoff -a'.")
    try:
        subprocess.run(["sudo", "swapoff", "-a"], check=True, capture_output=True, text=True)
        result["status"] = "PASS"
        result["message"] = "Swap has been turned off successfully."
        logging.info(result["message"])
    except subprocess.CalledProcessError as e:
        result["status"] = "FAIL"
        result["message"] = f"Failed to turn off swap: {e.stderr.strip() if e.stderr else str(e)}"
        logging.error(result["message"])
    return result

def set_swappiness_zero():
    """
    Set swappiness to 0 using sysctl and log the result.
    Swappiness controls how aggressively the kernel swaps memory pages.
    Setting it to 0 minimizes swapping, which is often desired for performance.
    """
    result = {"name": "Set Swappiness", "status": "", "message": ""}
    logging.info("Attempting to set vm.swappiness to 0.")
    try:
        subprocess.run(["sudo", "sysctl", "vm.swappiness=0"], check=True, capture_output=True, text=True)
        result["status"] = "PASS"
        result["message"] = "Swappiness has been set to 0 successfully."
        logging.info(result["message"])
    except subprocess.CalledProcessError as e:
        result["status"] = "FAIL"
        result["message"] = f"Failed to set swappiness: {e.stderr.strip() if e.stderr else str(e)}"
        logging.error(result["message"])
    return result

def main():
    """
    Main function to coordinate swap configuration steps.
    Logs the start and end of the process, and prints status to the console.
    """
    logging.info("Starting swap configuration process.")
    print("Starting to config Swap")
    swap_off_result = turn_swap_off()
    swappiness_result = set_swappiness_zero()
    logging.info(f"Swap off result: {swap_off_result}")
    logging.info(f"Swappiness result: {swappiness_result}")
    print("Swap configuration complete. Check log for details.")
    logging.info("Swap configuration process completed.")

if __name__ == "__main__":
    main()