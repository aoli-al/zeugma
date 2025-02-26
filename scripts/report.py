import os
import pathlib
import sys

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd

import extract
import report_util
import tables

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            font-family: Open Sans, sans-serif;
            color: black;
        }

        h2 {
            font-size: 20px;
            font-weight: 550;
            display: block;
        }

        h3 {
            font-size: 12px;
            display: block;
        }

        img {
            max-width: 100%;
            max-height: calc((100vh - 100px) * 1 / 2);
            width: auto;
            height: auto;
            object-fit: contain;
        }

        .wrapper {
            display: flex;
            overflow-x: scroll;
            gap: 20px;
        }

        table * {
            font-size: 10px;
            font-weight: normal;
            text-align: right;
            padding: 5px;
        }

        table {
            border-bottom: black 1px solid;
            border-top: black 1px solid;
            border-collapse: collapse;
        }
    </style>
    <title>Fuzzing Report</title>
</head>
<body>
<div>
    $content
</div>
</body>
</html>
"""


def find_dataset(input_dir, name):
    file = os.path.join(input_dir, f'{name}.csv')
    print(f'Checking for {name} data: {file}.')
    if os.path.isfile(file):
        print(f'\t{name.title()} data found.')
        return report_util.read_timedelta_csv(file)
    else:
        print(f'\t{name.title()} data not found.')
        return None


def create_pairwise_subsection(frames, name=''):
    content = ''.join(t.to_html() for t in frames)
    return f'<div><h3>{name}Pairwise P-Values and Effect Sizes</h3><div class="wrapper">{content}</div></div>'


def plot_coverage(data, subject, cmap):
    fuzzers = sorted(data['fuzzer'].unique())
    if cmap is None:
        cmap = {k[0]: k[1] for k in zip(fuzzers, [k for k in mcolors.TABLEAU_COLORS])}
    data = report_util.select(data, subject=subject)
    plt.rcParams["font.family"] = 'sans-serif'
    fig, ax = plt.subplots(figsize=(8, 4))
    stats = data.groupby(by=['time', 'fuzzer'])['covered_branches'] \
        .agg([min, max, 'median']) \
        .reset_index() \
        .sort_values('time')
    for fuzzer in fuzzers:
        color = cmap[fuzzer]
        selected = stats[stats['fuzzer'] == fuzzer]
        times = (selected['time'] / pd.to_timedelta(1, 'm')).tolist()
        ax.plot(times, selected['median'], color=color, label=fuzzer)
        ax.fill_between(times, selected['min'], selected['max'], color=color, alpha=0.2)
    ax.set_xlabel('Time (Minutes)')
    ax.set_ylabel('Covered Branches')
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    ax.set_title(subject.title())
    return fig


def create_plots_subsection(data):
    subjects = sorted(data['subject'].unique())
    fuzzers = sorted(data['fuzzer'].unique())
    cmap = {k[0]: k[1] for k in zip(fuzzers, [k for k in mcolors.TABLEAU_COLORS])}
    content = ''
    for subject in subjects:
        plot_coverage(data, subject, cmap)
        content += report_util.fig_to_html()
    legend = report_util.plot_legend(cmap, len(fuzzers))
    return f'<div><h3>Coverage Over Time</h3>{legend}<div class="wrapper">{content}</div></div>'


def create_coverage_content(data, times):
    return tables.create_coverage_table(data, times).to_html() + \
        create_pairwise_subsection(tables.create_coverage_pairwise(data, times)) + \
        create_plots_subsection(data)


def create_defects_content(data, times):
    if data.empty:
        return "<p>No matched defects detected.</p>"
    return tables.create_defect_table(data, times).to_html() + \
        create_pairwise_subsection(tables.create_defects_pairwise(data, times))


def create_heritability_content(data):
    return tables.create_heritability_table(data).to_html() + \
        create_pairwise_subsection(tables.create_hy_pairwise(data), 'HY ') + \
        create_pairwise_subsection(tables.create_ir_pairwise(data), 'IR ')


def create_section(name, content_f, **kwargs):
    print(f'Creating {name} section.')
    content = content_f(**kwargs)
    print(f'\tCreated {name} section.')
    return f'<div><h2>{name.title()}</h2>{content}</div>'


def write_report(report_file, content):
    print(f'Writing report to {report_file}.')
    os.makedirs(pathlib.Path(report_file).parent, exist_ok=True)
    report = TEMPLATE.replace('$content', content)
    with open(report_file, 'w') as f:
        f.write(report)
    print(f'\tSuccessfully wrote report.')


def create_report(input_dir, report_file):
    times = [pd.to_timedelta(5, 'm'), pd.to_timedelta(3, 'h')]
    coverage = find_dataset(input_dir, 'coverage')
    detections = find_dataset(input_dir, 'detections')
    # detections = None
    if coverage is None or detections is None:
        coverage, detections = extract.extract_data(input_dir, input_dir)
    content = create_section('coverage', create_coverage_content, data=coverage, times=times)
    content += create_section('defects', create_defects_content, data=detections, times=times)
    heritability = find_dataset(input_dir, 'heritability')
    if heritability is not None:
        content += create_section('heritability', create_heritability_content, data=heritability)
    write_report(report_file, content)


def main():
    create_report(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
