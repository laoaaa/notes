import subprocess
import tempfile
from pathlib import Path
import unittest
from publish import Publisher

class PublicationTests(unittest.TestCase):
    def test_publish_and_remote_divergence(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); remote = base/'remote.git'; local = base/'local'
            def run(*args, cwd=None):
                return subprocess.run(['git', *args], cwd=cwd, check=True,
                                      capture_output=True, text=True)
            run('init', '--bare', str(remote))
            run('init', '-b', 'main', str(local))
            run('config','user.name','Test',cwd=local)
            run('config','user.email','test@example.invalid',cwd=local)
            (local/'notes').mkdir();(local/'notes/a.md').write_text('one')
            run('add','.',cwd=local);run('commit','-m','Initial',cwd=local)
            run('remote','add','origin',str(remote),cwd=local)
            run('push','-u','origin','main',cwd=local)
            p=Publisher(local,['git']);p.prepare()
            (local/'notes/a.md').write_text('two');p.publish()
            self.assertEqual(p.git('rev-parse','HEAD'),p.git('rev-parse','origin/main'))
            (local/'unrelated.txt').write_text('private')
            with self.assertRaises(RuntimeError):p.prepare()
            (local/'unrelated.txt').unlink()
            other=base/'other';run('clone','--branch','main',str(remote),str(other))
            run('config','user.name','Test',cwd=other)
            run('config','user.email','test@example.invalid',cwd=other)
            p.prepare()
            (other/'remote.txt').write_text('remote')
            run('add','.',cwd=other);run('commit','-m','Concurrent',cwd=other)
            run('push',cwd=other)
            (local/'notes/a.md').write_text('three')
            with self.assertRaises(RuntimeError):p.publish()
            self.assertEqual((local/'notes/a.md').read_text(),'three')

if __name__=='__main__':unittest.main()
