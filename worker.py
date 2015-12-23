import os
from itertools import permutations
from job_queue import GridEngineQueue
from utils import (
    make_dir,
    checksum_match)
from caller import (
    MuTect,
    SomaticSniper,
    Strelka,
    VarScan)

class Somatic:
    def __init__(self, args):
        self.sample_file = args.infile
        self.ref = args.ref
        self.af_cutoff = args.af
        self.skip_on = args.skip_on
        self.chunk_on = args.chunk_on
        self.q = GridEngineQueue()
        self.script_dir = '{}/job_scripts'.format(
            os.path.dirname(os.path.realpath(__file__)))
        self.hold_jid = {}
        make_dir(self.out_dir)

    @property
    def worker_name(self):
        return type(self).__name__.lower()

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
        with open(self.sample_file) as f:
            for line in f:
                try:
                    clone, tissue = line.split()[:2]
                    yield (clone, tissue)
                except ValueError as e:
                    msg = 'Sample list file should have at least 2 columns.'
                    raise e(msg)

    @property
    def concall_file(self):
        return "{}/{}.snv_call_n4_{}AFcutoff.txt".format(
            self.out_dir, self.sample_name, str(self.af_cutoff).replace("0.", ""))

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

    def _concall(self, hold_jid):
        qopt = self._qopt('con_call', hold_jid)
        cmd =  '{}/snv_con_call.sh {} {} {} {}'.format(
            self.script_dir, self.sample_name, self.af_cutoff, self.af_dir, self.out_dir)
        return self.q.submit(qopt, cmd)

    def _skip_msg(self, msg):
        print('\x1b[2A', end='\r')
        print('\x1b[2K', end='\r')
        print('Skip {:>16} job: {}\n\n'.format(
            msg, self.sample_name))

    def _run_msg(self, msg):
        print('\x1b[2A', end='\r')
        print('\x1b[2K', end='\r')
        print('Submitted {:>11} job: {}\n\n'.format(
            msg, self.sample_name))

    def run(self):
        self._check_data()

        mt = MuTect(self.ref, self.worker_name, self.skip_on, self.chunk_on)
        sn = SomaticSniper(self.ref, self.worker_name, self.skip_on)
        st = Strelka(self.ref, self.worker_name, self.skip_on)
        vs = VarScan(self.ref, self.worker_name, self.skip_on, self.chunk_on)

        for clone, tissue in self.sample_list:
            mt.run(clone, tissue) 
            sn.run(clone, tissue)
            st.run(clone, tissue)
            vs.run(clone, tissue)

        for sample_name in mt.hold_jid:
            hold_jid = ','.join([jid
                                 for jid in [mt.hold_jid[sample_name],
                                             sn.hold_jid[sample_name],
                                             st.hold_jid[sample_name],
                                             vs.hold_jid[sample_name]]
                                 if jid != ''])
            self.sample_name = sample_name

            if self.concall_file_ok:
                self.hold_jid[self.sample_name] = ''
                self._skip_msg('con_call')
            else:
                make_dir(self.qerr_dir)
                make_dir(self.qout_dir)
                self.hold_jid[self.sample_name] = self._concall(hold_jid)
                self._run_msg('con_call')

    def end_msg(self):
        print('\x1b[2A', end='\r')
        print('\x1b[2K', end='\r')
        print('-' * 59)
        print('\x1b[2K', end='\r')
        print('mosaicnator.py submitted {} jobs in total.'.format(self.q.n_submit))

class Sensitivity(Somatic):
    def __init__(self, args):
        super().__init__(args)
        self.na12878 = args.bam

    @property
    def sample_list(self):
        with open(sample_file) as f:
            for line in f:
                try:
                    clone = line.split()[0]
                    yield (clone, self.na12878)
                except ValueError as e:
                    msg = 'Sample list file has empty line.'
                    raise e(msg)
        
    def _sensitivity(self, hold_jid):
        qopt = self._qopt('sens', hold_jid)
        cmd =  '{}/snv_sensitivity.sh {} {}'.format(
            self.script_dir, self.sample_name, self.out_dir)
        return self.q.submit(qopt, cmd)

    def run(self):
        super().run()
        for sample in self.hold_jid:
            hold_jid = self.hold_jid[sample_name]
            self.sample_name = sample_name
            self.hold_jid[self.sample_name] = self._sensitivity(hold_jid)

class Pairwise(Somatic):
    @property
    def sample_list(self):
        clones = []
        with open(sample_file) as f:
            for line in f:
                try:
                    clones.append(line.split()[0])
                except ValueError as e:
                    msg = 'Sample list file has empty line.'
                    raise e(msg)
        return permutations(clones, 2)

    def _exp_score(self):
        pass
