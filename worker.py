import os
import shutil
import subprocess
from job_queue import GridEngineQueue, LocalQueue
from utils import (
    make_qdir,
    make_dir,
    check_dir,
    check_bam_index,
    check_ref_index,
    check_ref_dict,
    check_outfile,
    read_header,
    read_body,
    read_vcf_header,
    read_vcf_body,
    get_chunk_intervals,
    get_samplename)


class SomaticCall:
    def __init__(self, ref, out_dir):
        check_ref_index(ref)
        check_ref_dict(ref)
        make_dir(out_dir)
        make_qdir()
        self.ref = ref
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)
        self.out_dir = out_dir
        self.exec_dir = os.path.dirname(os.path.realpath(__file__))
        self.q = GridEngineQueue()
    
    def _get_cmdpath(self, cmd):
        return os.path.join(self.exec_dir, 'job_scripts', cmd)

    def _run_mutect(self):
        cmd = self._get_cmdpath('mutect.sh')
        sub_name = self.out_name + '.mutect'
        out_dir = '{}/{}'.format(self.out_dir, sub_name)
        out_name = '{}/{}'.format(out_dir, sub_name)
        make_dir(out_dir)
        make_qdir(sub_name)

        for chrom, start, end in self.chunk_intervals:
            job_name = 'mutect.{}.{}-{}-{}'.format(
                self.out_name, chrom, start, end)
            interval = '{}:{}-{}'.format(
                chrom, start, end)
            q_opt_str = '-N {} -q 1-day -o q.out/{} -e q.err/{}'.format(
                job_name, sub_name, sub_name)
            cmd_str = '{} {} {} {} {} {}'.format(
                cmd, self.ref, self.clone, self.tissue, out_name, interval)
            self.q.submit(q_opt_str, cmd_str)

    def _run_somaticsniper(self):
        cmd = self._get_cmdpath('somaticsniper.sh')
        job_name = 'somaticsniper.{}'.format(self.out_name)
        out_name = '{}/{}.somaticsniper'.format(self.out_dir, self.out_name)
        q_opt_str = '-N {}'.format(job_name)
        cmd_str = '{} {} {} {} {}'.format(
            cmd, self.ref, self.clone, self.tissue, out_name)
        self.q.submit(q_opt_str, cmd_str)

    def _run_strelka(self):
        cmd = self._get_cmdpath('strelka.sh')
        job_name = 'strelka.{}'.format(self.out_name)
        out_name = '{}/{}.strelka'.format(self.out_dir, self.out_name)
        q_opt_str = '-N {}'.format(job_name)
        cmd_str = '{} {} {} {} {}'.format(
            cmd, self.ref, self.clone, self.tissue, out_name)
        self.q.submit(q_opt_str, cmd_str)

    def _run_varscan(self):
        cmd = self._get_cmdpath('varscan.sh')
        sub_name = self.out_name + '.varscan'
        out_dir = '{}/{}'.format(self.out_dir, sub_name)
        out_name = '{}/{}'.format(out_dir, sub_name)
        make_dir(out_dir)
        make_qdir(sub_name)

        for chrom, start, end in self.chunk_intervals:
            job_name = 'mutect.{}.{}-{}-{}'.format(
                self.out_name, chrom, start, end)
            interval = '{}:{}-{}'.format(
                chrom, start, end)
            q_opt_str = '-N {} -q 1-day -o q.out/{} -e q.err/{}'.format(
                job_name, sub_name, sub_name)
            cmd_str = '{} {} {} {} {} {}'.format(
                cmd, self.ref, self.clone, self.tissue, out_name, interval)
            self.q.submit(q_opt_str, cmd_str)

    def run(self, clone, tissue, out_name=None):
        check_bam_index(clone)
        check_bam_index(tissue)
        self.clone = clone
        self.tissue = tissue

        if out_name is None:
            self.out_name = get_samplename(clone)
        else:
            self.out_name = out_name

        self._run_somaticsniper()
        self._run_strelka()
        self._run_mutect()
        self._run_varscan()

    def wait(self):
        self.q.wait('somatic_call')

class PostProcess:
    def __init__(self, ref, data_dir):
        check_ref_index(ref)
        check_dir(data_dir)
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)
        self.data_dir = data_dir
        self.q = LocalQueue()
        
    def _post_mutect(self):
        data_dir = '{}/{}.mutect'.format(self.data_dir, self.sample_name)
        data_files = [
            '{}/{}.mutect.{}-{}-{}.txt'.format(
                data_dir, self.sample_name, chrom, start, end)
            for chrom, start, end in self.chunk_intervals]
        out_file = '{}/{}.mutect.txt'.format(self.data_dir, self.sample_name)

        check_outfile(out_file)
        with open(out_file, 'w') as out:
            for line in read_header(data_files[0], 2):
                out.write(line)
            for file in data_files:
                for line in read_body(file, 3):
                    if 'KEEP\n' in line:
                        out.write(line)
                        
        shutil.rmtree(data_dir)

    def _post_somaticsniper(self):
        data_file = '{}/{}.somaticsniper.vcf'.format(
            self.data_dir, self.sample_name)
        out_file = '{}/{}.somaticsniper.somatic.vcf'.format(
            self.data_dir, self.sample_name)
        
        check_outfile(out_file)
        with open(out_file, 'w') as out:
            for line in read_vcf_header(data_file):
                out.write(line)
            for line in read_vcf_body(data_file):
                somatic_status = line.split()[-1].split(':')[-2]
                if somatic_status == '2':
                    out.write(line)    

    def _post_strelka(self):
        data_dir = '{}/{}.strelka/chromosomes'.format(self.data_dir, self.sample_name)
        shutil.rmtree(data_dir)
        
    def _post_varscan_snv(self):
        data_dir = '{}/{}.varscan'.format(self.data_dir, self.sample_name)
        data_files = [
            '{}/{}.varscan.{}-{}-{}.snp'.format(
                data_dir, self.sample_name, chrom, start, end)
            for chrom, start, end in self.chunk_intervals]
        out_file = '{}/{}.varscan.snp'.format(data_dir, self.sample_name)
        
        check_outfile(out_file)
        with open(out_file, 'w') as out:
            for line in read_header(data_files[0]):
                out.write(line)
            for file in data_files:
                for line in read_body(file):
                    out.write(line)

        for file in data_files:
            os.remove(file)

        subprocess.run(['varscan', 'processSomatic',
                        out_file, '--p-value', '0.05'],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

    def _post_varscan_indel(self):
        data_dir = '{}/{}.varscan'.format(self.data_dir, self.sample_name)
        data_files = [
            '{}/{}.varscan.{}-{}-{}.indel'.format(
                data_dir, self.sample_name, chrom, start, end)
            for chrom, start, end in self.chunk_intervals]
        out_file = '{}/{}.varscan.indel'.format(data_dir, self.sample_name)
        
        check_outfile(out_file)
        with open(out_file, 'w') as out:
            for line in read_header(data_files[0]):
                out.write(line)
            for file in data_files:
                for line in read_body(file):
                    out.write(line)

        for file in data_files:
            os.remove(file)            
                    
        subprocess.run(['varscan', 'processSomatic',
                        out_file, '--p-value', '0.05'],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        
    def run(self, sample):
        self.sample_name = get_samplename(sample)
        
        self.q.call(self._post_mutect)
        self.q.call(self._post_somaticsniper)
        self.q.call(self._post_strelka)
        self.q.call(self._post_varscan_snv)
        self.q.call(self._post_varscan_indel)

    def wait(self):
        self.q.wait('postprocess')

class AlleleFreq:
    def __init__(self, data_dir, out_dir):
        self.data_dir = data_dir
        self.out_dir = out_dir
        self.q = LocalQueue()
        
    def wait(self):
        self.q.wait('AF calculation')
