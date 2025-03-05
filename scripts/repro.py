from multiprocessing import Pool
import os

CONFIGURATIONS = [
    #  "ant",
    #  "closure",
    #  "maven",
    #  "rhino",
    #  "chocopy",
    #  "gson",
    "jackson"

]
ALGOS = [
    "ei",
    "zest",
    "zeugma-linked",
    "bedivfuzz-simple",
    "bedivfuzz-structure",
]


def get_commands():

    for config in CONFIGURATIONS:
        for algo in ALGOS:
            for iter in range(0, 8):
                command = f"mvn -pl :zeugma-evaluation-tools meringue:analyze -P{config},{algo} -Dmeringue.outputDirectory=/data/aoli/havoc_eval/cov-test/{config}-{algo}-results-{iter}"
                yield command

with Pool(1) as p:
    p.map(os.system, get_commands())
