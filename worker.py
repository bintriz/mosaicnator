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
        make_dir(out_dir)
        self.out_dir = out_dir
        check_ref_index(ref)
        check_ref_dict(ref)
        self.ref = ref
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)
        make_qdir()
        self.q = GridEngineQueue()
        self.exec_dir = os.path.dirname(os.path.realpath(__file__))
    
    def _get_cmdpath(self, cmd):
        return os.path.join(self.exec_dir, 'job_scripts', cmd)

    def _run_mutect(self):
        cmd = self._get_cmdpath('run_mutect_chunk.sh')
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
        cmd = self._get_cmdpath('run_somaticsniper.sh')
        job_name = 'somaticsniper.{}'.format(self.out_name)
        out_name = '{}/{}.somaticsniper'.format(self.out_dir, self.out_name)
        q_opt_str = '-N {}'.format(job_name)
        cmd_str = '{} {} {} {} {}'.format(
            cmd, self.ref, self.clone, self.tissue, out_name)
        self.q.submit(q_opt_str, cmd_str)

    def _run_strelka(self):
        cmd = self._get_cmdpath('run_strelka.sh')
        job_name = 'strelka.{}'.format(self.out_name)
        out_name = '{}/{}.strelka'.format(self.out_dir, self.out_name)
        q_opt_str = '-N {}'.format(job_name)
        cmd_str = '{} {} {} {} {}'.format(
            cmd, self.ref, self.clone, self.tissue, out_name)
        self.q.submit(q_opt_str, cmd_str)

    def _run_varscan(self):
        cmd = self._get_cmdpath('run_varscan_chunk.sh')
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
        check_dir(data_dir)
        self.data_dir = data_dir
        check_ref_index(ref)
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)
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
        
        self._post_mutect()
        self._post_somaticsniper()
        self._post_strelka()
        self._post_varscan_snv()
        self._post_varscan_indel()

    def wait(self):
        self.q.wait('postprocess')

class AlleleFreq:
    def __init__(self, ref, data_dir, out_dir):
        check_ref_index(ref)
        self.ref = ref
        check_dir(data_dir)
        self.data_dir = data_dir
        make_dir(out_dir)
        self.out_dir = out_dir
        self.q = GridEngineQueue()
        self.exec_dir = os.path.dirname(os.path.realpath(__file__))
    
    def _cmdpath(self, cmd):
        return os.path.join(self.exec_dir, 'job_scripts', cmd)

    def _datadir(self, caller):
        return '{}/{}.{}'.format(self.data_dir, self.sample_name, caller)

    def _snv_call_file(self, caller):
        if caller == 'mutect':
            call_file = '{}.mutect.keep.txt'.format(self.sample_name)
        elif caller == 'somaticsniper':
            call_file = '{}.somaticsniper.somatic.vcf'.format(self.sample_name)
        elif caller == 'strelka':
            call_file = 'results/passed.somatic.snvs.vcf'
        elif caller == 'varscan':
            call_file = '{}.varscan.snp.Somatic.hc'.format(self.sample_name)
        return '{}/{}'.format(self._datadir(caller), call_file)
    
    def _snv_coord_file(self, caller):
        return '{}/{}.{}.snv_coord.txt'.format(self.out_dir, self.sample_name, caller)

    def _snv_coord_qopt(self, caller, hold_jid=None):
        job_name = '{}_snv_coord.{}'.format(caller, self.sample_name)
        if hold_jid == None:
            q_opt_str = '-N {}'.format(job_name)
        else:
            q_opt_str = '-N {} -hold_jid {}'.format(job_name, hold_jid)
        return q_opt_str

    def _snv_coord_cmd(self, caller):
        return self._cmdpath('snv_coord_{}.sh'.format(caller))
        
    def _snv_coord_submit(self, caller, hold_jid=None):
        call_file = self._snv_call_file(caller)
        coord_file = self._snv_coord_file(caller)
        q_opt_str = self._snv_coord_qopt(caller, hold_jid)
        cmd_str = '{} {} {}'.format(
            self._snv_coord_cmd(caller), call_file, coord_file)
        submit_jid = self.q.submit(q_opt_str, cmd_str)
        return submit_jid

    def _snv_AF_file(self, caller):
        return '{}/{}.{}.snv_AF.txt'.format(self.out_dir, self.sample_name, caller)
        
    def _snv_AF_qopt(self, caller, hold_jid=None):
        job_name = '{}_snv_AF.{}'.format(caller, self.sample_name)
        if hold_jid == None:
            q_opt_str = '-N {}'.format(job_name)
        else:
            q_opt_str = '-N {} -hold_jid {}'.format(job_name, hold_jid)
        return q_opt_str
    
    def _snv_AF_submit(self, caller, hold_jid=None):
        coord_file = self._snv_coord_file(caller)
        af_file = self._snv_AF_file(caller)
        q_opt_str = self._snv_AF_qopt(caller, hold_jid)
        cmd_str = '{} {} {} {} {} {}'.format(
            self._cmdpath('snv_af.sh'), self.ref, self.clone, self.tissue, coord_file, af_file)
        submit_jid = self.q.submit(q_opt_str, cmd_str)
        return submit_jid

    def run(self, clone, tissue):
        self.sample_name = get_samplename(clone)
        self.clone = clone
        self.tissue = tissue

        self._snv_AF_submit('mutect', self._snv_coord_submit('mutect'))
        self._snv_AF_submit('somaticsniper', self._snv_coord_submit('somaticsniper'))
        self._snv_AF_submit('strelka', self._snv_coord_submit('strelka'))
        self._snv_AF_submit('varscan', self._snv_coord_submit('varscan'))
