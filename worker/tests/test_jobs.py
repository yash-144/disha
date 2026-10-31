import unittest

try:
    from worker.jobs.outbox_dispatch import run_outbox_dispatch
except ImportError:
    from jobs.outbox_dispatch import run_outbox_dispatch

class TestWorkerJobs(unittest.TestCase):
    def test_outbox_job_defined(self):
        self.assertTrue(callable(run_outbox_dispatch))

if __name__ == '__main__':
    unittest.main()
