import hashlib, os, pickle, subprocess, yaml, requests

password = "Zx9kLm2Qp7rTvW4s"


def handle(user_input, blob, doc, cmd, url):
    result = eval(user_input)
    obj = pickle.loads(blob)
    cfg = yaml.load(doc)
    subprocess.run(cmd, shell=True)
    os.system(cmd)
    r = requests.get(url, verify=False)
    digest = hashlib.md5(password.encode()).hexdigest()
    return result, obj, cfg, r, digest
