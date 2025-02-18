import sys
import os
from typing import Dict, Iterator, List, Any, Set
import numpy as np
import pandas as pd
import seaborn as sns
import re
import sns_configs
from matplotlib.patches import Patch
import matplotlib.pyplot as plt


def p2f(value: str) -> float:
    return float(value.strip('%'))

def log_scale_index(max: int) -> Iterator[int]:
    idx = 1
    while idx < max:
        yield idx
        if idx > 500:
            idx += 1000
        else:
            idx *= 2

def name_converter(value: str) -> int:
    return int(value.split("_")[1])

def build_corpus_time_map(path: str) -> Dict[str, int]:
    pattern = re.compile(r"\[(\d+)\] Saved.*corpus/(id_\d+) .*")
    mapping = {}
    with open(os.path.join(path, "fuzz.log")) as f:
        for line in f:
            result = pattern.match(line)
            if result:
                mapping[result.group(2)] = int(result.group(1))
    return mapping

def name_to_time_mapping(corpus_map: Dict[str, str], value: str) -> int:
    key = "id_" + value.split("_")[1]
    return corpus_map[key] // 1000
    # return int()


def load_processing_time_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(os.path.join(path, "results.csv"), sep=",", names=["case", "result", "class", "cov", 'time'],
                       converters={"case": name_converter}, skiprows=10)
    experiment_name = os.path.basename(path)
    algorithm = "-".join(experiment_name.split('-')[1:-2])
    algorithm = map_algorithm(algorithm)
    data['algorithm'] = [algorithm] * data.shape[0]
    return data


def build_cov_data_over_time(path: str, indices) -> pd.DataFrame:
    corpus_map = build_corpus_time_map(path)
    data = pd.read_csv(os.path.join(path, "results.csv"), sep=",", names=["# unix_time", "result", "class", "all_covered_probes", 'time'],
                       converters={"# unix_time": lambda v: name_to_time_mapping(corpus_map, v)})
    data['# unix_time'] -= data["# unix_time"][0]
    data['# unix_time'] //= 60 * 10
    data = data.copy().drop_duplicates(
        keep='last', subset=["# unix_time"])
    data['# unix_time'] *= 10
    data = data.set_index("# unix_time").reindex(indices).interpolate().reset_index()
    return data


def map_algorithm(algo: str) -> str:
    if "mix-testWithGenerator" in algo:
        return "$\\textsc{Gex}_m$"
    if "mix-testWithReversedGenerator" in algo:
        return "Mix-Rev"
    if algo == "zest-fast" or algo == "zest-testWithGenerator":
        return "Zest"
    if algo == "zest-testWithReversedGenerator":
        return "Zest-Rev"
    if algo == "ei-fast" or algo == "ei-testWithGenerator":
        return "EI"
    if algo == "ei-testWithReversedGenerator":
        return "EI-Rev"
    if "ei-no-havoc" in algo:
        return "$\\textsc{Gex}$"
    if algo == "mix-no-havoc":
        return "Mix-No-Havoc"
    if "blind" in algo:
        return "Blind"
    print(algo)
    return algo

def color_mapping(algo: str) -> str:
    pass

def process_plot_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(os.path.join(path, "plot_data"), sep=",", skipinitialspace=True)
    data['# unix_time'] -= data["# unix_time"][0]
    data['# unix_time'] //= 60 * 10
    data['total_inputs'] = data['valid_inputs'] + data['invalid_inputs']
    experiment_name = os.path.basename(path)
    algorithm = "-".join(experiment_name.split('-')[1:-2])
    algorithm = map_algorithm(algorithm)
    x_axis = "# unix_time"
    time_based_data = data.copy().drop_duplicates(
        keep='last', subset=[x_axis])
    time_based_data['# unix_time'] *= 10
    time_based_data['algorithm'] = [algorithm] * time_based_data.shape[0]
    x_axis = "total_inputs"
    cov_data = build_cov_data_over_time(path, time_based_data["# unix_time"].values.tolist())
    time_based_data["all_covered_probes"] = cov_data["all_covered_probes"].values.tolist()

    return time_based_data, None


INTERESTING = [
    'org/mozilla/javascript',
    'com/google/javascript',
    'org/apache/maven/model',
    'org/apache/tools/ant',
    'org/apache/bcel/verifier',
    'chocopy/reference'
    # "org/codehaus/plexus/util/xml", "org/apache/maven/model",
    # "com/sun/org/apache/xerces", "org/apache/tools/ant",
    # "com/google/javascript/jscomp/parsing", "com/google/javascript/jscomp/",
    # "org/mozilla/javascript/Parser", "org/mozilla/javascript/",
    # "org/apache/bcel/classfile", " org/apache/bcel/verifier"
]


def process_cov_data(path: str) -> Set[str]:
    result = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                # for pattern in INTERESTING:
                #     if pattern in line or True:
                result.add(line)
    return result

def generate_plot_data_base(path: str, data: pd.DataFrame, x_axis: str, y_axis: str, step=1, x_label: str = None, y_label: str = None):
    print(x_axis, y_axis)
    axis = sns.lineplot(x=x_axis, y=y_axis, hue='algorithm',
                        hue_order=sorted(data['algorithm'].unique()),
                        style_order=sorted(data['algorithm'].unique()), data=data)
    axis.set(xlabel = x_label)
    axis.set(ylabel = y_label)
    fig = axis.get_figure()
    fig.savefig(path, bbox_inches='tight', pad_inches=0.1)
    fig.clf()

def generate_valid_coverage_over_time(path: str, data: pd.DataFrame, step=1):
    generate_plot_data_base(path, data, "# unix_time", "valid_covered_probes", step)

def generate_all_coverage_over_time(path: str, data: pd.DataFrame, step=1):
    generate_plot_data_base(path, data, "# unix_time", "all_covered_probes", step, "Time (min)", "Branch Coverage")

def generate_total_inputs_over_time(path: str, data: pd.DataFrame, step=1):
    generate_plot_data_base(path, data, "# unix_time", "total_inputs", step, "Time (min)", "Total Inputs")

def generate_valid_coverage_over_total_inputs(path: str, data: pd.DataFrame, step=1):
    generate_plot_data_base(path, data, "total_inputs", "valid_covered_probes", step)

def generate_all_coverage_over_total_inputs(path: str, data: pd.DataFrame, step=1):
    generate_plot_data_base(path, data, "total_inputs", "all_covered_probes", step)

def generate_coverage_delta_hist(path: str, data: pd.DataFrame):
    bins =list(range(-10, 11))
    axis = sns.histplot(data=data, bins=bins, color=sns_configs.colors[0], discrete=True)
    ylim = max(np.histogram(data[0].to_numpy(), bins=bins)[0]) + 10
    axis.set_xticks(range(-10, 12, 2))
    axis.set_xticklabels([10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10])
    axis.set(xlim=(-10, 10))
    axis.set(ylim=(0, ylim))
    f1 = axis.fill_between([0, 10], y1=[ylim, ylim], alpha=0.3, facecolor=sns_configs.colors[-3], hatch="X", linewidth=0.0)
    f2 = axis.fill_between([-10, 0], y1=[ylim, ylim], alpha=0.3, facecolor=sns_configs.colors[-2], hatch=".", linewidth=0.0)
    axis.legend([f1, f2], ["EI", "Zest"])
    if "closure" in path:
        axis.set(ylabel = "# branches")
    else:
        axis.set(ylabel = None)
    fig = axis.get_figure()
    fig.savefig(path, bbox_inches='tight')
    fig.clf()


def generate_corpus_exec_time(path: str, data: pd.DataFrame):
    # cls = ['#2A587A', '#FABC75', '#83B828', '#F83A25', '#FDD8EB']
    # # colors = ['#648FFF', '#FFB000', '#DC267F','#FE6100', '#785EF0']
    # palette = sns.color_palette(cls)
    colors = ['#4C72B0', '#DD8452', '#F83A25', '#FDD8EB']
    # colors = ['#648FFF', '#FFB000', '#DC267F','#FE6100', '#785EF0']
    sns.set_palette(sns.color_palette(colors), 5, 1)
    bins = 20
    axis = sns.histplot(data=data, x="time", hue="algorithm", multiple="dodge", bins=bins, log_scale=(False, True), alpha=1,
                        hue_order=sorted(data['algorithm'].unique()))

    patches = axis.patches
    colors = [patch.get_facecolor() for patch in patches]
    print(colors)

    textures = ['\\', '/', 'o']
    for i, bar in enumerate(axis.patches):
        bar.set_hatch(textures[i // bins])


    patch_1 = Patch(label='Zest', hatch=textures[0], facecolor=colors[0])
    patch_2 = Patch(label='$\\textsc{Gex}$', hatch=textures[1], facecolor=colors[-1])

    axis.set(xlabel = "Execution Time (ms)", ylabel = "Count")


    fig = axis.get_figure()
    axis.legend(handles=[patch_2, patch_1], loc='upper right')
    # axis.legend()
    plt.show()
    fig.savefig(path, bbox_inches='tight', pad_inches=0.1)
    fig.clf()
    # generate_plot_data_base(path, data, "case", "time", 1)

def show_values_on_bars(axs):
    def _show_on_single_plot(ax):
        for p in ax.patches:
            _x = p.get_x() + p.get_width() / 2
            _y = p.get_y() + p.get_height() + 10
            value = str(int(p.get_height()))
            ax.text(_x, _y, value, ha="center")

    if isinstance(axs, np.ndarray):
        for _, ax in np.ndenumerate(axs):
            _show_on_single_plot(ax)
    else:
        _show_on_single_plot(axs)

def generate_total_coverage_bar(path: str, data: Dict[str, List[Any]]):
    axis = sns.barplot(x="type", y="value", hue="algo", data=data)
    show_values_on_bars(axis)
    fig = axis.get_figure()
    fig.savefig(path)
    fig.clf()



