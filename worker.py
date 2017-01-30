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
    Scalpel,
    Strelka,
    VarScan)

class Somatic:
    def __init__(self, args):
        self.sample_file = args.infile
        self.var_type = args.var_type
        self.min_af = args.min_AF
        self.skip_on = args.skip_on
        self.chunk_size = args.chunk_size
            
        self.q = GridEngineQueue()
        self.hold_jid = {}
        
        self._regist_caller(args)
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
    def bin_path(self):
        return os.path.dirname(os.path.realpath(__file__))

    @property
    def script_dir(self):
        return '{}/job_scripts/{}'.format(self.bin_path, self.worker_name)
        
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
                clone, tissue = line.strip().split('\t')[:2]
                pairs.add((clone, tissue))
        return pairs
    
    @property
    def concall_file(self):
        return '{}/{}.{}_call_n{}_{}AFcutoff.txt'.format(
            self.out_dir, self.sample_name, self.var_type,
            len(self.caller), str(self.min_af).replace('0.', ''))

    @property
    def concall_file_ok(self):
        return self.skip_on and checksum_match(self.concall_file)

    @property
    def chunk_file(self):
        f=lambda n,i=0:"{:.0f}{}".format(n," kMG"[i])*(n<1e3)or f(n/1e3, i+1)
        return "{}.call/genomic_regions_{}_chunk.txt".format(
            self.worker_name, f(self.chunk_size).strip())

    @property
    def chrom_file(self):
        return "{}.call/genomic_regions_chrom.txt".format(self.worker_name)

    def _regist_caller(self, args):
        if self.var_type == "snv":
            self.caller = [SomaticSniper(args, self.worker_name),
                           Strelka(args, self.worker_name)]
            if args.chunk_on:
                self.caller.extend([
                    MuTect(args, self.worker_name, self.chunk_file),
                    VarScan(args, self.worker_name, self.chunk_file)])
            else:
                self.caller.extend([
                    MuTect(args, self.worker_name),
                    VarScan(args, self.worker_name)])
                
        elif self.var_type == "indel":
            self.caller = [Strelka(args, self.worker_name)]
            if args.chunk_on:
                self.caller.extend([
                    Scalpel(args, self.worker_name, self.chrom_file),
                    VarScan(args, self.worker_name, self.chunk_file)])
            else:
                self.caller.extend([
                    Scalpel(args, self.worker_name),
                    VarScan(args, self.worker_name)])

    def _prepare_dir(self):
        make_dir(self.out_dir)
        
    def _qopt(self, jprefix, hold_jid=''):
        qopt = '-N {}.{} -e {} -o {} -v BIN_PATH={}'.format(
            jprefix, self.sample_name, self.qerr_dir, self.qout_dir, self.bin_path)
        if hold_jid == '':
            return qopt
        else:
            return qopt + ' -hold_jid {}'.format(hold_jid)

    def _concall(self, hold_jid):
        qopt = self._qopt('con_call', hold_jid)
        cmd =  '{}/{}_con_call.sh {} {} {}'.format(
            self.script_dir, self.var_type,
            self.min_af, self.af_dir, self.concall_file)
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
        for clone, tissue in self.sample_list:
            self.clone = clone
            self.tissue = tissue
            self._run()
        end_msg(self.q.j_total)

class Sensitivity(Somatic):
    def __init__(self, args):
        super().__init__(args)
        self.control_bam = args.control_bam
        self.control_var = args.control_var
        self.g1k_var = args.g1k_var
        self.germ_het_var = args.germ_het_var
        
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
                clone = line.strip().split('\t')[0]
                pairs.add((clone, self.control_bam))
        return pairs

    @property
    def concall_file(self):
        return '{}/{}.call_n{{}}.{}_AF.txt'.format(
            self.af_dir, self.sample_name, self.var_type)

    @property
    def concall_file_ok(self):
        return self.skip_on and all(
            [checksum_match(self.concall_file.format(i))
             for i in range(1,len(self.caller)+1)])

    @property
    def true_file(self):
        if self.var_type == "snv":
            var_type = "snp"
        else:
            var_type = self.var_type
        return '{}/germ_het_not_in_NA12878_{}.txt'.format(
            self.out_dir, var_type)
    
    @property
    def true_file_ok(self):
        return self.skip_on and checksum_match(self.true_file)

    @property
    def sens_file(self):
        return "{}/{}.{}_sensitivity_{}AFcutoff.txt".format(
            self.out_dir, self.sample_name, self.var_type,
            str(self.min_af).replace('0.', ''))
    
    @property
    def sens_file_ok(self):
        return self.skip_on and checksum_match(self.sens_file)

    def _concall(self, hold_jid):
        qopt = self._qopt('con_call', hold_jid)
        cmd =  '{}/{}_con_call.sh {} {} {}'.format(
            self.script_dir, self.var_type,
            self.min_af, self.af_dir, self.sample_name)
        return self.q.submit(qopt, cmd)

    def _truefile(self):
        qopt = '-N true_file -e q.err -o q.out'
        cmd =  '{}/true_file.sh {} {} {} {}'.format(
            self.script_dir, self.control_var, self.g1k_var,
            self.germ_het_var, self.true_file)
        return self.q.submit(qopt, cmd)
    
    def _sensitivity(self, hold_jid):
        qopt = self._qopt('sens', hold_jid)
        cmd =  '{}/{}_sensitivity.sh {} {} {} {}'.format(
            self.script_dir, self.var_type,
            self.min_af, self.true_file, self.af_dir, self.sens_file)
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
                clones.add(line.strip().split('\t')[0])
        return permutations(clones, 2)

    @property
    def concall_dir(self):
        return '{}/concall'.format(self.out_dir)

    @property
    def concall_file(self):
        return '{}/{}.{}_call_n{}_{}AFcutoff.txt'.format(
            self.concall_dir, self.sample_name, self.var_type,
            len(self.caller), str(self.min_af).replace('0.', ''))

    @property
    def explscore_file(self):
        return '{}/{}pairwise_union.{}_call_n{}_{}AFcutoff.expl_score.txt'.format(
            self.out_dir, self.out_prefix, self.var_type,
            len(self.caller), str(self.min_af).replace('0.',''))
    @property
    def explscore_file_ok(self):
        return self.skip_on and checksum_match(self.explscore_file)

    def _prepare_dir(self):
        make_dir(self.concall_dir)
        
    def _explscore(self, hold_jid):
        concall_flist = '{}/{}concall_list.{}_call_n{}_{}AFcutoff.txt'.format(
            self.out_dir, self.out_prefix, self.var_type,
            len(self.caller), str(self.min_af).replace('0.',''))
        with open(concall_flist, 'w') as out:
            for clone, tissue in self.sample_list:
                self.clone = clone
                self.tissue = tissue
                out.write(self.concall_file + '\n')
        qopt = '-N expl_score -e q.err -o q.out -v BIN_PATH={}'.format(self.bin_path)
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
            jids = []
            for clone, tissue in self.sample_list:
                self.clone = clone
                self.tissue = tissue
                jids.append(super()._run())
            hold_jid = ','.join(jid for jid in jids if jid != '')
            self._explscore(hold_jid)
            self._run_msg('expl_score')
            end_msg(self.q.j_total)
