with open(".env", "r") as f:
    lines = f.readlines()
with open(".env", "w") as f:
    for line in lines:
        if line.startswith("AGGREGATOR_URL="):
            f.write("AGGREGATOR_URL=http://host.docker.internal:20128\n")
        else:
            f.write(line)
