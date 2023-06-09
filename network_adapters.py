import subprocess


def get_all_nic_details():
    output = subprocess.check_output(
        ["netsh", "interface", "ipv4", "show", "interface"]
    )

    output_str = ""
    try:
        output_str = output.decode(errors="ignore")
    except Exception:
        pass

    nic_list = []
    for line in output_str.split("\n"):
        line = line.strip()
        if (
            ("connected" in line)
            and ("Loopback" not in line)
            and ("disconnected" not in line)
        ):
            parts = line.split()
            try:
                nic_list.append(
                    {
                        "index": int(parts[0]),
                        "metric": int(parts[1]),
                        "status": parts[3],
                        "name": " ".join([n for n in parts[4:]]),
                    }
                )
            except Exception:
                pass

    get_additional_nic_details(nic_list)

    return nic_list


def get_additional_nic_details(nic_list):
    # Run the 'ipconfig' command and capture its output
    output = subprocess.check_output(["ipconfig", "/all"])
    # Convert the output to a string
    output_str = ""
    try:
        output_str = output.decode(errors="ignore")
    except Exception:
        pass

    # Separate result for each network adapter
    output_parts = output_str.split("\r\n\r\n")

    for nic in nic_list:
        try:
            report = None
            i = 0
            while i < len(output_parts):
                if f"adapter {nic['name']}:" in output_parts[i]:
                    report = output_parts[i] + "\r\n" + output_parts[i + 1]
                    details = extract_nic_details_from_report(report)
                    nic["dns_servers"] = details["dns_servers"]
                    nic["dhcp_server"] = details["dhcp_server"]
                    nic["default_gateway"] = details["default_gateway"]
                    break
                i = i + 1
        except Exception:
            pass


def extract_nic_details_from_report(report):
    dns_servers = []
    dhcp_server = None
    default_gateway = None

    if "DNS Servers . . . . . . . . . . . :" in report:
        try:
            i = 0
            report_lines = report.split("\n")
            while i < len(report_lines):
                line = report_lines[i]
                if "DNS Servers" in line:
                    dns_servers.append(line.strip().split(":")[1].strip())
                    if i < len(report_lines) - 1:
                        next_line = report_lines[i + 1]
                        next_line_parts = next_line.split(":")
                        if len(next_line_parts) == 1 and len(next_line.strip()) > 0:
                            dns_servers.append(next_line.strip())
                i = i + 1
        except Exception:
            pass

    try:
        dhcp_server = [
            line.strip().split(":")[1].strip()
            for line in report.split("\n")
            if "DHCP Server" in line
        ][0]
    except Exception:
        pass

    try:
        default_gateway = [
            line.strip().split(":")[1].strip()
            for line in report.split("\n")
            if "Default Gateway" in line
        ][0]
    except Exception:
        pass

    return {
        "dns_servers": dns_servers,
        "dhcp_server": dhcp_server,
        "default_gateway": default_gateway,
    }


def get_default_route_gateway():
    output = subprocess.check_output(["route", "print"])
    # Convert the output to a string
    output_str = ""
    try:
        output_str = output.decode(errors="ignore")
    except Exception:
        pass

    lines = output_str.split("\r\n")
    for line in lines:
        try:
            parts = line.strip().split()
            if parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                return parts[2]
        except Exception:
            pass

    return None


def detect_default_network_interface():
    nics = get_all_nic_details()
    default_route_gateway = get_default_route_gateway()

    if default_route_gateway:
        for nic in nics:
            if nic.get("default_gateway") == default_route_gateway:
                return nic["name"]

    try:
        result = nics[0]
        for nic in nics:
            if nic["status"] == "connected" and result["status"] == "disconnected":
                result = nic
            elif nic["status"] == "connected" and nic["metric"] < result["metric"]:
                result = nic

        return result["name"]
    except Exception:
        return None
