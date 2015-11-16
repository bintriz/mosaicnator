import os
from job_queue import Queue
from utils import (
    check_qdir,
    check_dir,
    check_bam_index,
    check_ref_index,
    get_chunk_intervals)


class Caller(object):
    def __init__(self, ref, out_dir):
        check_ref_index(ref)
        check_dir(out_dir)
        check_qdir()
        self.ref = ref
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)
        self.out_dir = out_dir
        self.cmd_dir = os.path.dirname(os.path.realpath(__file__))
    
    def _get_cmdpath(self, cmd):
        return os.path.join(self.cmd_dir, cmd)

    def _run_mutect(self, clone, tissue):
        cmd = self._get_cmdpath('mutect.sh')
        sub_name = self.out_name + '.mutect'
        out_dir = '{}/{}'.format(self.out_dir, sub_name)
        out_name = '{}/{}'.format(out_dir, sub_name)
        check_dir(out_dir)
        check_qdir(sub_name)

        for chrom, start, end in self.chunk_intervals:
            job_name = 'mutect.{}.{}-{}-{}'.format(
                self.out_name, chrom, start, end)
            interval = '{}:{}-{}'.format(
                chrom, start, end)
            q_opt_str = '-N {} -q 1-day -o q.out/{} -e q.err/{}'.format(
                job_name, sub_name, sub_name)
            cmd_str = '{} {} {} {} {} {}'.format(
                cmd, self.ref, clone, tissue, out_name, interval)
            Queue().submit(q_opt_str, cmd_str)

    def _run_somaticsniper(self, clone, tissue):
        cmd = self._get_cmdpath('somaticsniper.sh')
        job_name = 'somaticsniper.{}'.format(self.out_name)
        out_name = '{}/{}.somaticsniper'.format(self.out_dir, self.out_name)
        q_opt_str = '-N {}'.format(job_name)
        cmd_str = '{} {} {} {} {}'.format(
            cmd, self.ref, clone, tissue, out_name)
        Queue().submit(q_opt_str, cmd_str)

    def _run_strelka(self, clone, tissue):
        cmd = self._get_cmdpath('strelka.sh')
        job_name = 'strelka.{}'.format(self.out_name)
        out_name = '{}/{}.strelka'.format(self.out_dir, self.out_name)
        q_opt_str = '-N {}'.format(job_name)
        cmd_str = '{} {} {} {} {}'.format(
            cmd, self.ref, clone, tissue, out_name)
        Queue().submit(q_opt_str, cmd_str)

    def _run_varscan(self, clone, tissue):
        cmd = self._get_cmdpath('varscan.sh')
        sub_name = self.out_name + '.varscan'
        out_dir = '{}/{}'.format(self.out_dir, sub_name)
        out_name = '{}/{}'.format(out_dir, sub_name)
        check_dir(out_dir)
        check_qdir(sub_name)

        for chrom, start, end in self.chunk_intervals:
            job_name = 'mutect.{}.{}-{}-{}'.format(
                self.out_name, chrom, start, end)
            interval = '{}:{}-{}'.format(
                chrom, start, end)
            q_opt_str = '-N {} -q 1-day -o q.out/{} -e q.err/{}'.format(
                job_name, sub_name, sub_name)
            cmd_str = '{} {} {} {} {} {}'.format(
                cmd, self.ref, clone, tissue, out_name, interval)
            Queue().submit(q_opt_str, cmd_str)

#    def _post_mutect(self):

#    def _post_somaticsniper(self):

#    def _post_varscan(self):

    def run(self, clone, tissue, out_name=None):
        check_bam_index(clone)
        check_bam_index(tissue)

        if out_name is None:
            self.out_name = os.path.splitext(os.path.basename(clone))[0]
        else:
            self.out_name = out_name

        self._run_somaticsniper(clone, tissue)
        self._run_strelka(clone, tissue)
        self._run_mutect(clone, tissue)
        self._run_varscan(clone, tissue)

    def postprocess(self):
        self._post_mutect()
        self._post_somaticsniper()
        self._post_varscan()
