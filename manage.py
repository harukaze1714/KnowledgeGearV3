import sys
sys.dont_write_bytecode = True

from flask_script import Command
from flask_script import Manager

import app
import db

class InitDB(Command):
    def run(self):
        db.create_all()

if __name__ == '__main__':
    m = Manager(app)
    m.add_command('init_db', InitDB())
    m.run()

