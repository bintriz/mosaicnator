import os
from itertools import permutations
from job_queue import GridEngineQueue
from utils import (
    make_dir,
    checksum_match,
    skip_msg,
    run_msg,
    end_msg)
from caller import (
    MuTect,
    SomaticSniper,
    Strelka,
    VarScan)

class Somatic:
    def __init__(self, args):
        self.sample_file = args.infile
        self.ref = args.ref
        self.refidx = args.ref + '.fai'
        self.min_af = args.min_AF
        self.skip_on = args.skip_on
        self.caller = [
            SomaticSniper(
                self.ref, self.worker_name, args.min_MQ, args.min_BQ,
                self.skip_on),
            Strelka(
                self.ref, self.worker_name, args.min_MQ, args.min_BQ,
                self.skip_on)]
        
        if args.chunk_on:
            self.chunk_size = 25000000
            self._chunkfile()
            self.caller.extend([
                MuTect(
                    self.ref, self.worker_name, args.min_MQ, args.min_BQ,
                    self.skip_on, self.chunk_file),
                VarScan(
                    self.ref, self.worker_name, args.min_MQ, args.min_BQ,
                    self.skip_on, self.chunk_file)])
        else:
            self.caller.extend([
                MuTect(
                    self.ref, self.worker_name, args.min_MQ, args.min_BQ,
                    self.skip_on),
                VarScan(
                    self.ref, self.worker_name, args.min_MQ, args.min_BQ,
                    self.skip_on)])
            
        self.q = GridEngineQueue()
        self.script_dir = '{}/job_scripts'.format(
            os.path.dirname(os.path.realpath(__file__)))
        self.hold_jid = {}
        self._prepare_dir()

    @property
    def worker_name(self):
        return type(self).__name__.lower()

    @property
    def sample_name(self):
        clname = os.path.splitext(os.path.basename(self.clone))[0]
        tiname = os.path.splitext(os.path.basename(self.tissue))[0]
        return '{}_-_{}'.format(clname, tiname)

    @property
    def qerr_dir(self):
        return 'q.err/{}.all'.format(self.sample_name)

    @property
    def qout_dir(self):
        return 'q.out/{}.all'.format(self.sample_name)

    @property
    def af_dir(self):
        return self.worker_name + '.AF'

    @property
    def out_dir(self):
        return self.worker_name + '.out'

    @property
    def sample_list(self):
        pairs = set()
        with open(self.sample_file) as f:
            for line in f:
                try:
                    clone, tissue = line.split()[:2]
                    pairs.add((clone, tissue))
                except ValueError as e:
                    msg = 'Sample list file should have at least 2 columns.'
                    raise e(msg)
        return pairs

    @property
    def chunk_file(self):
        return '{}.call/chunk_regions.txt'.format(self.worker_name)
    
    @property
    def concall_file(self):
        return '{}/{}.snv_call_n4_{}AFcutoff.txt'.format(
            self.out_dir, self.sample_name, str(self.min_af).replace('0.', ''))

    @property
    def concall_file_ok(self):
        return self.skip_on and checksum_match(self.concall_file)

    @staticmethod
    def _check_ref(fasta):
        if not os.path.isfile(fasta):
            msg = "Can't find the reference file '{}'".format(fasta)
            raise FileNotFoundError(msg)
        if not os.path.isfile(fasta + '.fai'):
            msg = "Can't find index for the fasta file '{}'".format(fasta)
            raise FileNotFoundError(msg)
        refname = os.path.splitext(fasta)[0]
        if not os.path.isfile(refname + '.dict'):
            msg = "Can't find dictionary for the fasta file '{}'".format(fasta)
            raise FileNotFoundError(msg)

    @staticmethod
    def _check_bam(bam):
        if not os.path.isfile(bam):
            msg = "Can't find the bam file '{}'".format(bam)
            raise FileNotFoundError(msg)

        bamname = os.path.splitext(bam)[0]
        if not os.path.isfile(bamname + '.bai') and not os.path.isfile(bamname + '.bam.bai'):
            msg = "Can't find index for the bam file '{}'".format(bam)
            raise FileNotFoundError(msg)

    def _prepare_dir(self):
        make_dir(self.out_dir)
        
    def _check_data(self):
        self._check_ref(self.ref)
        for clone, tissue in self.sample_list:
            self._check_bam(clone)
            self._check_bam(tissue)
    
    def _qopt(self, jprefix, hold_jid=''):
        qopt = '-N {}.{} -e {} -o {}'.format(
            jprefix, self.sample_name, self.qerr_dir, self.qout_dir)
        if hold_jid == '':
            return qopt
        else:
            return qopt + ' -hold_jid {}'.format(hold_jid)

    def _chunkfile(self):
        make_dir(os.path.dirname(self.chunk_file))
        with open(self.chunk_file, 'w') as out:
            with open(self.refidx) as f:
                for line in f:
                    chrom, chrom_size = line.split()[:2]
                    chrom_size = int(chrom_size)
                    for start in range(1, chrom_size, self.chunk_size):
                        end = start + self.chunk_size - 1
                        if end > chrom_size:
                            end = chrom_size
                        out.write('{}:{}-{}\n'.format(chrom, start, end))

    def _concall(self, hold_jid):
        qopt = self._qopt('con_call', hold_jid)
        cmd =  '{}/snv_con_call.sh {} {} {}'.format(
            self.script_dir, self.min_af, self.af_dir, self.concall_file)
        return self.q.submit(qopt, cmd)

    def _skip_msg(self, jname):
        if self.q.__class__.is_1st_print:
            self.q.__class__.is_1st_print = False
        else:
            print('\x1b[2A', end='\r')
        skip_msg(jname, '{}.all'.format(self.sample_name))

    def _run_msg(self, jname):
        run_msg(jname, '{}.all'.format(self.sample_name))

    def _run(self):
        hold_jid = ''
        if self.concall_file_ok:
            self._skip_msg('calling')
            self._skip_msg('af_calc')
            self._skip_msg('con_call')
        else:
            make_dir(self.qerr_dir)
            make_dir(self.qout_dir)
            jids = (caller.run(self.clone, self.tissue) for caller in self.caller)
            hold_jid = ','.join(jid for jid in jids if jid != '')
            hold_jid = self._concall(hold_jid)
            self._run_msg('con_call')
        return hold_jid
            
    def run(self):
        self._check_data()
        for clone, tissue in self.sample_list:
            self.clone = clone
            self.tissue = tissue
            self._run()
        end_msg(self.q.j_total)
        
class Sensitivity(Somatic):
    def __init__(self, args):
        super().__init__(args)
        self.control_bam = args.control_bam
        self.control_snp = args.control_snp
        self.g1k_snp = args.g1k_snp
        self.germ_het_snp = args.germ_het_snp
        
        if self.true_file_ok:
            self.true_jid = ''
            self.q.__class__.is_1st_print = False
            skip_msg('truefile', 'For all samples')
        else:
            self.true_jid = self._truefile()
            run_msg('truefile', 'For all samples')
            
    @property
    def sample_list(self):
        pairs = set()
        with open(self.sample_file) as f:
            for line in f:
                try:
                    clone = line.split()[0]
                    pairs.add((clone, self.control_bam))
                except ValueError as e:
                    msg = 'Sample list file has empty line.'
                    raise e(msg)
        return pairs

    @property
    def concall_file(self):
        return '{}/{}.call_n{{}}.snv_AF.txt'.format(
            self.af_dir, self.sample_name)

    @property
    def concall_file_ok(self):
        return self.skip_on and all(
            [checksum_match(self.concall_file.format(i)) for i in range(1,5)])

    @property
    def true_file(self):
        return '{}/germ_het_not_in_NA12878_snp.txt'.format(self.out_dir)
    
    @property
    def true_file_ok(self):
        return self.skip_on and checksum_match(self.true_file)

    @property
    def sens_file(self):
        return "{}/{}.snv_sensitivity_{}AFcutoff.txt".format(
            self.out_dir, self.sample_name, str(self.min_af).replace('0.', ''))
    
    @property
    def sens_file_ok(self):
        return self.skip_on and checksum_match(self.sens_file)

    def _concall(self, hold_jid):
        qopt = self._qopt('con_call', hold_jid)
        cmd =  '{}/snv_con_call_for_sensitivity.sh {} {} {}'.format(
            self.script_dir, self.min_af, self.af_dir, self.sample_name)
        return self.q.submit(qopt, cmd)

    def _truefile(self):
        qopt = '-N true_file -e q.err -o q.out'
        cmd =  '{}/snv_true_file_for_sensitivity.sh {} {} {} {}'.format(
            self.script_dir, self.control_snp, self.g1k_snp,
            self.germ_het_snp, self.true_file)
        return self.q.submit(qopt, cmd)
    
    def _sensitivity(self, hold_jid):
        qopt = self._qopt('sens', hold_jid)
        cmd =  '{}/snv_sensitivity.sh {} {} {} {}'.format(
            self.script_dir, self.min_af, self.true_file, 
            self.af_dir, self.sens_file)
        return self.q.submit(qopt, cmd)

    def _run(self):
        if self.sens_file_ok:
            self._skip_msg('calling')
            self._skip_msg('af_calc')
            self._skip_msg('con_call')
            self._skip_msg('sens')
        else:
            make_dir(self.qerr_dir)
            make_dir(self.qout_dir)
            
            hold_jid = super()._run()
            if hold_jid == '':
                hold_jid = self.true_jid
            elif self.true_jid != '':
                hold_jid += ',' + self.true_jid
                
            self._sensitivity(hold_jid)
            self._run_msg('sens')

class Pairwise(Somatic):    
    def __init__(self, args):
        super().__init__(args)
        self.out_prefix = args.out_prefix
        if self.out_prefix != '':
            self.out_prefix += '-'

    @property
    def sample_list(self):
        clones = set()
        with open(self.sample_file) as f:
            for line in f:
                try:
                    clones.add(line.split()[0])
                except ValueError as e:
                    msg = 'Sample list file has empty line.'
                    raise e(msg)
        return permutations(clones, 2)

    @property
    def concall_dir(self):
        return '{}/concall'.format(self.out_dir)

    @property
    def concall_file(self):
        return '{}/{}.snv_call_n4_{}AFcutoff.txt'.format(
            self.concall_dir, self.sample_name, str(self.min_af).replace('0.', ''))

    @property
    def explscore_file(self):
        return '{}/{}pairwise_snv_union.snv_call_n4_{}AFcutoff.explanation_score.txt'.format(
            self.out_dir, self.out_prefix, str(self.min_af).replace('0.',''))
    @property
    def explscore_file_ok(self):
        return self.skip_on and checksum_match(self.explscore_file)

    def _prepare_dir(self):
        make_dir(self.concall_dir)
        
    def _explscore(self, hold_jid):
        concall_flist = '{}/{}concall_list.snv_call_n4_{}AFcutoff.txt'.format(
            self.out_dir, self.out_prefix, str(self.min_af).replace('0.',''))
        with open(concall_flist, 'w') as out:
            for clone, tissue in self.sample_list:
                self.clone = clone
                self.tissue = tissue
                out.write(self.concall_file + '\n')
        qopt = '-N expl_score -e q.err -o q.out'
        if hold_jid != '':
            qopt += ' -hold_jid {}'.format(hold_jid)
        cmd =  '{}/expl_score.sh {} {}'.format(
            self.script_dir, concall_flist, self.explscore_file)
        return self.q.submit(qopt, cmd)

    def run(self):
        if self.explscore_file_ok:
            self._skip_msg('calling')
            self._skip_msg('af_calc')
            self._skip_msg('con_call')
            self._skip_msg('expl_score')
        else:
            self._check_data()
            jids = []
            for clone, tissue in self.sample_list:
                self.clone = clone
                self.tissue = tissue
                jids.append(super()._run())
            hold_jid = ','.join(jid for jid in jids if jid != '')
            self._explscore(hold_jid)
            self._run_msg('expl_score')
            end_msg(self.q.j_total)
