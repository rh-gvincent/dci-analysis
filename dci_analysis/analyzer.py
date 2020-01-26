# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import glob
import logging
import os
import sys

import numpy
import pandas as pd


LOG = logging.getLogger(__name__)

formatter = logging.Formatter('%(levelname)s - %(message)s')
streamhandler = logging.StreamHandler(stream=sys.stdout)
streamhandler.setFormatter(formatter)
LOG.addHandler(streamhandler)
LOG.setLevel(logging.DEBUG)


def get_jobs_dataset(topic_name):
    csv_files = glob.glob('%s/*' % topic_name)
    first_csf_file, csv_files = csv_files[0], csv_files[1:]
    abs_path_cf = os.path.abspath(first_csf_file)
    jobs_dataset = pd.read_csv(abs_path_cf, delimiter=',', engine='python', index_col='testname')  # noqa

    for cf in csv_files:
        abs_path_cf = os.path.abspath(cf)
        df = pd.read_csv(abs_path_cf, delimiter=',', engine='python', index_col='testname')  # noqa
        jobs_dataset = jobs_dataset.merge(
            df, left_on='testname', right_on='testname')
    return jobs_dataset


def write_series_csv(file_path, series, header):
    with open(file_path, 'w') as f:
        f.write('%s\n' % header)
        for tc, time in series.items():
            f.write('%s,%s\n' % (tc, time))


def analyze(topic_name_1, topic_name_2):
    # compute standard deviation
    LOG.info('compute standard deviation')
    for topic_name in (topic_name_1, topic_name_2):
        jobs_dataset = get_jobs_dataset(topic_name)
        jobs_std = jobs_dataset.apply(numpy.std, axis=1)
        jobs_std.sort_values(ascending=False, inplace=True)
        file_path = '%s_standard_deviation.csv' % topic_name
        LOG.info('write file to %s' % file_path)
        write_series_csv(file_path, jobs_std, 'testname, time')

    # compare baseline mean with jobs
    LOG.info('compare the mean of topic %s with jobs of topic %s...' % (topic_name_1, topic_name_2))  # noqa
    baseline_jobs = get_jobs_dataset(topic_name_1)
    baseline_jobs_mean = baseline_jobs.mean(axis=1)

    jobs = get_jobs_dataset(topic_name_2)

    def delta_mean(lign):
        if lign.name not in baseline_jobs.keys():
            return "N/A"
        diff = lign - baseline_jobs_mean[lign.name]
        return (diff * 100.0) / baseline_jobs_mean[lign.name]

    compared_jobs = jobs.apply(delta_mean, axis=1)
    file_path = '%s_mean_vs_%s.csv' % (topic_name_1, topic_name_2)
    LOG.info('write file to %s' % file_path)
    compared_jobs.to_csv(file_path, sep=',')

    # compare baseline median with jobs
    LOG.info('compare the median of topic %s with jobs of topic %s...' % (topic_name_1, topic_name_2))  # noqa
    baseline_jobs_median = baseline_jobs.median(axis=1)

    jobs = get_jobs_dataset(topic_name_2)

    def delta_median(lign):
        if lign.name not in baseline_jobs.keys():
            return "N/A"
        diff = lign - baseline_jobs_median[lign.name]
        return (diff * 100.0) / baseline_jobs_median[lign.name]

    compared_jobs = jobs.apply(delta_median, axis=1)
    file_path = '%s_median_vs_%s.csv' % (topic_name_1, topic_name_2)
    LOG.info('write file to %s' % file_path)
    compared_jobs.to_csv(file_path, sep=',')
