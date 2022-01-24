import subprocess
import json


# limit in GB and conversion to GiB
limitGB = "100"
limitGB = int(limitGB)
limit = limitGB * 0.93
limit = str(limit)


def get_modem_status(modem, config):
    # getting usage data for current monthly period and converting it to a string
    useless_cat_call = subprocess.Popen(["vnstat", "--json", "m", "--iface", config["interface"]],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
    output, errors = useless_cat_call.communicate()
    useless_cat_call.wait()
    print(">>", output)
    print(">>", errors)

    print("STATE", type(output), output)

    return {"modem": modem, "vnstat": json.loads(output)}
