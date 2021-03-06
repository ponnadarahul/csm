# =============================================================================
# Copyright (c) 2015, Cisco Systems, Inc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
# =============================================================================
import time
import threading 
import sys

from database import DBSession

from models import Host
from models import logger
from models import InventoryJob
from models import InventoryJobHistory
from models import SystemOption

from constants import JobStatus
from threadpool import Pool
from threadpool import WorkUnit

from handlers.loader import get_inventory_handler_class 
from base import InventoryContext
from utils import create_log_directory

import traceback
    
lock = threading.Lock()
in_progress_jobs = {}

class InventoryManager(threading.Thread):
    def __init__(self, name, num_threads=None):
        threading.Thread.__init__(self, name = name)
        
        if num_threads is None:
            num_threads = SystemOption.get(DBSession()).inventory_threads
        
        # Set up the thread pool
        self.pool = Pool(num_threads)
        
    def run(self):
        while 1:
            # This will be configurable
            time.sleep(20)
            self.dispatch()
     
    def dispatch(self):
        db_session = DBSession()
        try:
            inventory_jobs = db_session.query(InventoryJob).filter(InventoryJob.pending_submit == True).all()

            if len(inventory_jobs)> 0:
                for inventory_job in inventory_jobs:
                    self.submit_job(inventory_job.id)
        except:
            logger.exception('Unable to dispatch inventory job')  
        finally:
            db_session.close()
            
    def submit_job(self, job_id):

        with lock:
            # If another inventory job for the same host is already in progress,
            # the inventory job will not be queued for processing
            if job_id in in_progress_jobs:
                return False
            
        in_progress_jobs[job_id] = job_id
        self.pool.submit(InventoryWorkUnit(job_id))

        return True

 
class InventoryWorkUnit(WorkUnit):
    def __init__(self, job_id):
        self.job_id = job_id
    
    def process(self):
        
        db_session = DBSession()
        host_id = None
        inventory_job = None
        ctx = None
        try:
            
            inventory_job = db_session.query(InventoryJob).filter(InventoryJob.id == self.job_id).first()    
            if inventory_job is None:
                logger.error('Unable to retrieve inventory job: %s' % self.job_id)
                return
            
            host_id = inventory_job.host_id
            host = db_session.query(Host).filter(Host.id == host_id).first()
            if host is None:
                logger.error('Unable to retrieve host: %s' % host_id)
            
            handler_class = get_inventory_handler_class(host.platform)
            if handler_class is None:
                logger.error('Unable to get handler for %s, inventory job %s', host.platform, self.job_id)
            
            inventory_job.set_status(JobStatus.PROCESSING)
            inventory_job.session_log = create_log_directory(host.connection_param[0].host_or_ip, inventory_job.id)
            db_session.commit()         
            
            # Delegates the get_software logic to the handler
            ctx = InventoryContext(host, db_session, inventory_job)

            handler = handler_class()
            handler.execute(ctx)
            
            if ctx.success:
                archive_inventory_job(db_session, inventory_job, JobStatus.COMPLETED)
            else:
                # removes the host object as host.packages may have been modified.
                db_session.expunge(host)
                archive_inventory_job(db_session, inventory_job, JobStatus.FAILED)
            
            # Reset the pending retrieval flag
            inventory_job.pending_submit = False
            db_session.commit()

        except:
            try:
                logger.exception('InventoryManager hit exception - inventory job = %s', self.job_id)
                archive_inventory_job(db_session, inventory_job, JobStatus.FAILED, trace=sys.exc_info)
                # Reset the pending retrieval flag
                inventory_job.pending_submit = False
                db_session.commit()
            except:
                logger.exception('InventoryManager hit exception - inventory job = %s', self.job_id)
        finally:
            with lock:
                if self.job_id is not None and self.job_id in in_progress_jobs: del in_progress_jobs[self.job_id]
            db_session.close()       

def archive_inventory_job(db_session, inventory_job, job_status, trace=None):
    inventory_job.set_status(job_status)
    
    hist = InventoryJobHistory()
    hist.host_id = inventory_job.host_id
    hist.set_status(job_status)
    hist.session_log = inventory_job.session_log
        
    if trace is not None:
        hist.trace = traceback.format_exc()
    
    db_session.add(hist)

if __name__ == '__main__':
    pass
    