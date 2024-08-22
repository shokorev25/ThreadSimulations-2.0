import os
import subprocess


def check_service_status(service_name):
    try:
        output = subprocess.check_output(f"systemctl status {service_name}", shell=True)
        return "active" in output.decode("utf-8")
    except Exception:
        return False


def services(archive_name, main_path):

    service_file = f"/etc/systemd/system/{archive_name}_publisher.service"

    with open(service_file, "w") as f:
        with open(f"{main_path}/sample.txt", "r") as template:
            path_to_publisher = os.path.join(main_path, "publisher.py")
            text = template.read().replace('ExecStart=/usr/bin/python3',
                                           f'ExecStart=/usr/bin/python3 {path_to_publisher} {archive_name}')
            f.write(text)

    subprocess.run(["sudo", "systemctl", "enable", service_file])
    subprocess.run(["sudo", "systemctl", "start", f"{archive_name}_publisher.service"])
