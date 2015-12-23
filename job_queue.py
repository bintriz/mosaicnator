import subprocess
import xml.etree.ElementTree as ET
import time


class GridEngineQueue:
    _subq = {}
    is_1st_print = True

    def __init__(self, max_submit=8000):
        self.max_submit = max_submit

    @property
    def n_submit(self):
        return len(self.__class__._subq)

    @property
    def n_submit_in_q(self):
        return (self._subq_jstate_count('r') +
                self._subq_jstate_count('qw') +
                self._subq_jstate_count('hqw'))

    @property
    def n_done(self):
        return self._subq_jstate_count('done')

    @property
    def n_total_in_q(self):
        return len(self._allq)

    @property
    def n_run(self):
        return self._allq_jstate_count('r')

    @property
    def n_wait(self):
        return (self._allq_jstate_count('qw') +
                self._allq_jstate_count('hqw'))
        
    def _update(self):
        xmlstr = subprocess.check_output(['qstat', '-xml']).decode('utf-8')
        root = ET.fromstring(xmlstr)

        self._allq = {}
        for job in root.findall('./*/job_list'):
            jid = job.find('JB_job_number').text
            jname = job.find('JB_name').text
            jstate = job.find('state').text
            self._allq[jid] = {'name':jname, 'state':jstate}

        for jid in self.__class__._subq:
            self.__class__._subq[jid]['state'] = self._allq_jstate(jid)

    def _print_summary(self):
        qstat = '  queue status: {:>5} in total  {:>5} in run {:>5} in wait'.format(
            self.n_total_in_q, self.n_run, self.n_wait)
        jstat = 'submitted jobs: {:>5} submitted {:>5} done   {:>5} in queue'.format(
            self.n_submit, self.n_done, self.n_submit_in_q)
        if self.__class__.is_1st_print == True:
            self.__class__.is_1st_print = False
        else:
            print('\x1b[2A', end='\r')
        print('\x1b[2K', end='\r')
        print('-' * 59)
        print('\x1b[2K', end='\r')
        print(qstat)
        print('\x1b[2K', end='\r')
        print(jstat, end='\r')
        

    def _allq_wait(self):
        while True:
            self._update()
            if self.n_total_in_q < self.max_submit:
                return
            self._print_summary()
            time.sleep(5)

    def _allq_jstate(self, jid):
        try:
            return self._allq[jid]['state']
        except KeyError:
            return 'done'

    def _allq_jstate_count(self, jstate):
        allq_jstate_list = [jinfo['state'] for jinfo in self._allq.values()]
        return allq_jstate_list.count(jstate)        

    def _subq_jstate_count(self, jstate):
        subq_jstate_list = [jinfo['state'] for jinfo in self.__class__._subq.values()]
        return subq_jstate_list.count(jstate)        

    def submit(self, q_opt_str, cmd_str):
        self._allq_wait()
        qsub_cmd_list = ["qsub"] + q_opt_str.split() + cmd_str.split()
        stdout = subprocess.check_output(qsub_cmd_list).decode('utf-8')

        jid = stdout.split()[2]
        jname = (stdout.split()[3])[2:-2]
        self.__class__._subq[jid] = {'name':jname}

        self._update()
        self._print_summary()
        return jid
