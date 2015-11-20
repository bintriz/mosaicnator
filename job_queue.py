import multiprocessing as mp
import subprocess
import xml.etree.ElementTree as ET
import time


class GridEngineQueue:
    subq = {}

    def __init__(self, max_submit=8000):
        self.max_submit = max_submit
        
    def _update(self):
        xmlstr = subprocess.check_output(['qstat', '-xml']).decode('utf-8')
        root = ET.fromstring(xmlstr)

        self._allq = {}
        for job in root.findall('./*/job_list'):
            jid = job.find('JB_job_number').text
            jname = job.find('JB_name').text
            jstate = job.find('state').text
            self._allq[jid] = {'name':jname, 'state':jstate}

        for jid in self.__class__.subq:
            self.__class__.subq[jid]['state'] = self._allq_jstate(jid)

    def _print_jstate(self):
        n_submit = len(self.__class__.subq)
        n_q = len(self._allq)
        n_done = self._subq_jstate_count('done')
        n_run = self._allq_jstate_count('r')
        n_wait = self._allq_jstate_count('qw')
        outstr = '{} submitted: {} done, {} in queue({} in run, {} in wait)'
        print('\x1b[2K', end='\r')
        print(outstr.format(n_submit, n_done, n_q, n_run, n_wait), end='\r')

    def _allq_wait(self):
        while True:
            self._update()
            if len(self._allq) < self.max_submit:
                return
            self._print_jstate()
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
        subq_jstate_list = [jinfo['state'] for jinfo in self.__class__.subq.values()]
        return subq_jstate_list.count(jstate)        

    def test_submit(self, q_opt_str, cmd_str):
        print('qsub {} {}'.format(q_opt_str, cmd_str))

    def submit(self, q_opt_str, cmd_str):
        self._allq_wait()
        qsub_cmd_list = ["qsub"] + q_opt_str.split() + cmd_str.split()
        stdout = subprocess.check_output(qsub_cmd_list).decode('utf-8')

        jid = stdout.split()[2]
        jname = (stdout.split()[3])[2:-2]
        self.__class__.subq[jid] = {'name':jname}

        self._update()
        self._print_jstate()

    def wait(self, job_name=''):
        while True:
            self._update()
            n_done = self._subq_jstate_count('done')

            if  n_done == len(self.__class__.subq):
                self._print_jstate()

                if job_name != '':
                    print('\nAll {} jobs done'.format(job_name))
                else:
                    print('\nAll jobs done')

                self.__class__.subq = {}
                return

            self._print_jstate()
            time.sleep(5)

class LocalQueue:
    def __init__(self, max_submit=None):
        cpu_n = mp.cpu_count()
        if max_submit == None or max_submit > cpu_n:
            self.max_submit = cpu_n
        else:
            self.max_submit = max_submit

        self.q = []

    def _update(self):
        for p in self.q:
            if not p.is_alive():
                self.q.remove(p)

    def _q_wait(self):
        while True:
            self._update()
            if len(self.q) < self.max_submit:
                return
            time.sleep(3)
            
    def submit(self, cmd_str):
        self._q_wait()
        p = mp.Process(
            target=lambda x: subprocess.run(x, shell=True),
            args=(cmd_str,))
        p.start()
        self.q.append(p)

    def call(self, f):
        self._q_wait()
        p= mp.Process(target=f)
        p.start()
        self.q.append(p)
        
    def wait(self, job_name=''):
        while True:
            self._update()
            if len(self.q) == 0:
                if job_name != '':
                    print('All {} jobs done'.format(job_name))
                else:
                    print('All jobs done')
                return
            time.sleep(3)
            
