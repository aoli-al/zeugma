import json
import os
import pathlib
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

FAILURES_FILE_NAME = 'failures.json'
SUMMARY_FILE_NAME = 'summary.json'
COVERAGE_FILE_NAME = 'coverage.csv'


@dataclass(order=True, frozen=True)
class StackTraceElement:
    """Represents an element in a Java stack trace."""
    declaringClass: str
    fileName: str = None
    methodName: str = None
    lineNumber: int = -1

    def __repr__(self):
        if self.lineNumber == -2:
            x = 'Native Method'
        elif self.fileName is None:
            x = "Unknown Source"
        elif self.lineNumber >= 0:
            x = f"{self.fileName}:{self.lineNumber}"
        else:
            x = self.fileName
        return f"{self.declaringClass}.{self.methodName}({x})"


class Campaign:
    """Represents the results of a fuzzing campaign."""

    def __init__(self, campaign_dir):
        self.id = os.path.basename(campaign_dir)
        self.coverage_file = os.path.join(campaign_dir, COVERAGE_FILE_NAME)
        self.summary_file = os.path.join(campaign_dir, SUMMARY_FILE_NAME)
        self.failures_file = os.path.join(campaign_dir, FAILURES_FILE_NAME)
        self.valid = all(os.path.isfile(f) for f in [self.coverage_file, self.summary_file, self.failures_file])
        if self.valid:
            with open(self.summary_file, 'r') as f:
                summary = json.load(f)
                self.subject = summary['configuration']['testClassName'].split('.')[-1].replace('Fuzz', '')
                self.fuzzer = Campaign.get_fuzzer(summary)
                self.duration = summary['configuration']['duration']

    @staticmethod
    def get_fuzzer(summary):
        fuzzer = summary['frameworkClassName'].split('.')[-1].replace('Framework', '')
        if fuzzer == 'BeDivFuzz':
            fuzzer = 'BeDiv'
            if '-Djqf.div.SAVE_ONLY_NEW_STRUCTURES=true' in summary['configuration']['javaOptions']:
                fuzzer += '-Struct'
            else:
                fuzzer += '-Simple'
        elif fuzzer == 'Zeugma':
            crossover_type = 'X'
            for opt in summary['configuration']['javaOptions']:
                if opt.startswith('-Dzeugma.crossover='):
                    crossover_type = opt[len('-Dzeugma.crossover='):].title()
            fuzzer += "-" + crossover_type.replace('Linked', 'Link') \
                .replace('One_Point', '1PT') \
                .replace('Two_Point', '2PT') \
                .replace('None', 'X')
        return fuzzer

    def add_trial_info(self, df):
        df['subject'] = self.subject
        df['campaign_id'] = self.id
        df['fuzzer'] = self.fuzzer

    def get_coverage_data(self):
        df = pd.read_csv(self.coverage_file) \
            .rename(columns=lambda x: x.strip())
        df['time'] = pd.to_timedelta(df['time'], 'ms')
        self.add_trial_info(df)
        return df

    def get_failure_data(self):
        with open(self.failures_file, 'r') as f:
            records = json.load(f)
        if len(records) == 0:
            df = pd.DataFrame([], columns=['type', 'trace', 'detection_time', 'inducing_inputs'])
        else:
            df = pd.DataFrame.from_records(records) \
                .rename(columns=lambda x: x.strip())
            df['type'] = df['failure'].apply(lambda x: x['type'])
            df['trace'] = df['trace'] = df['failure'].apply(
                lambda x: tuple(map(lambda y: StackTraceElement(**y), x['trace'])))
            df['detection_time'] = pd.to_timedelta(df['firstTime'], 'ms')
            df = df.rename(columns={'inducingInputs': 'inducing_inputs'})
            df = df[['type', 'trace', 'detection_time', 'inducing_inputs']]
        self.add_trial_info(df)
        return df


def find_campaigns(input_dir):
    print(f'Searching for campaigns in {input_dir}.')
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir)]
    campaigns = list(map(Campaign, filter(os.path.isdir, files)))
    print(f"\tFound {len(campaigns)} campaigns.")
    return campaigns


def check_campaigns(campaigns):
    print(f'Checking campaigns.')
    result = []
    for c in campaigns:
        if not c.valid:
            print(f"\tMissing required files for {c.id}.")
        else:
            result.append(c)
    print(f'\t{len(result)} campaigns were valid.')
    return result


def read_campaigns(input_dir):
    return check_campaigns(find_campaigns(input_dir))


def resample(data, time_index):
    data = data.copy() \
        .set_index('time') \
        .sort_index()
    # Create a placeholder data frame indexed at the sample times filled with NaNs
    placeholder = pd.DataFrame(np., index=time_index, columns=data.columns)
    # Combine the placeholder data frame with the original
    # Replace the NaN's in placeholder with the last value at or before the sample time in the original
    data = data.combine_first(placeholder).ffill().fillna(0)
    # Drop times not in the resample index
    return data.loc[data.index.isin(time_index)] \
        .reset_index() \
        .rename(columns={'index': 'time'}) \
        .drop_duplicates(subset=['time'])


def create_coverage_csv(campaigns, times):
    duration = max(times)
    # Create an index from 0 to duration (inclusive) with 1000 sample times
    index = pd.timedelta_range(start=pd.Timedelta(0, 'ms'), end=duration, closed=None, periods=1000)
    # Ensure that the specified times are included in the index
    index = index.union(pd.TimedeltaIndex(sorted(times)))
    # Resample the data for each campaign at the index times
    return pd.concat([resample(c.get_coverage_data(), index) for c in campaigns]) \
        .reset_index()


def create_failures_table(campaigns):
    failures = pd.concat([t.get_failure_data() for t in campaigns]) \
        .reset_index(drop=True) \
        .sort_values(['subject', 'type', 'trace'])
    # Read known failures
    with open(os.path.join(pathlib.Path(__file__).parent.parent, 'data', 'failures.json'), 'r') as f:
        known_failures = json.load(f)
    for f in known_failures:
        f['trace'] = tuple(map(lambda y: StackTraceElement(**y), f['trace']))
    # Match failures against known failures which have been manually mapped to defects
    return pd.merge(failures, pd.DataFrame.from_records(known_failures), on=["subject", "type", "trace"], how="left")


def create_detections_table(campaigns):
    # 1. Read detected failure
    # 2. Remove failures not manually mapped to defects
    # 3. Transform each associated defect into a row
    # 4. Simplify column names.
    # 5. Remove rows for failures associated with no defects
    # 6. Find the first detection of each defect for each campaign
    # 7. Flatten the table and select desired columns
    return create_failures_table(campaigns) \
        .dropna(subset=['associatedDefects']) \
        .explode('associatedDefects') \
        .rename(columns={'associatedDefects': 'defect', 'detection_time': 'time'}) \
        .dropna(subset=['defect']) \
        .groupby(['campaign_id', 'fuzzer', 'defect', 'subject']) \
        .min() \
        .reset_index()[['campaign_id', 'fuzzer', 'subject', 'defect', 'time']]


def create_defects_csv(campaigns):
    # Find the first detection of each defect for each campaign
    detections = create_detections_table(campaigns)
    # If a campaign never detected a particular defect, fill in NaT
    defect_pairs = detections[['defect', 'subject']].drop_duplicates().itertuples(index=False, name=None)
    rows = []
    for defect, subject in defect_pairs:
        rows.extend([c.id, c.fuzzer, c.subject, defect, pd.NaT] for c in campaigns if c.subject == subject)
    return pd.DataFrame(rows, columns=['campaign_id', 'fuzzer', 'subject', 'defect', 'time']) \
        .set_index(['campaign_id', 'fuzzer', 'subject', 'defect']) \
        .combine_first(detections.set_index(['campaign_id', 'fuzzer', 'subject', 'defect'])) \
        .reset_index() \
        .sort_values(by=['campaign_id', 'defect'])


def extract_coverage_data(campaigns, times, output_dir):
    file = os.path.join(output_dir, 'coverage.csv')
    print('Creating coverage CSV.')
    coverage = create_coverage_csv(campaigns, times)
    coverage.to_csv(file, index=False)
    print(f'\tWrote coverage CSV to {file}.')
    return coverage


def extract_detections_data(campaigns, output_dir):
    file = os.path.join(output_dir, 'detections.csv')
    print('Creating defect detections CSV.')
    defects = create_defects_csv(campaigns)
    defects.to_csv(file, index=False)
    print(f'\tWrote defects detections CSV to {file}.')
    return defects


def extract_data(input_dir, output_dir):
    times = [pd.to_timedelta(5, 'm'), pd.to_timedelta(3, 'h')]
    campaigns = read_campaigns(input_dir)
    os.makedirs(output_dir, exist_ok=True)
    return extract_coverage_data(campaigns, times, output_dir), extract_detections_data(campaigns, output_dir)


def main():
    extract_data(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
