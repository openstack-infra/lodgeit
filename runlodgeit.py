from lodgeit.application import make_app
from lodgeit.utils import ctx
from lodgeit.database import session
from werkzeug import script
from werkzeug.serving import run_simple
from werkzeug.utils import create_environ, run_wsgi_app

dburi = 'sqlite:////tmp/lodgeit.db'

def run_app(app, path='/'):
    env = create_environ(path)
    return run_wsgi_app(app, env)

action_runserver = script.make_runserver(
    lambda: make_app(dburi),
    use_reloader=True)

action_shell = script.make_shell(
    lambda: {
        'app': make_app(dburi, False, True),
        'ctx': ctx,
        'session': session,
        'run_app': run_app
    },
    ('\nWelcome to the interactive shell environment of LodgeIt!\n'
     '\n'
     'You can use the following predefined objects: app, ctx, session.\n'
     'To run the application (creates a request) use *run_app*.')
)

if __name__ == '__main__':
    script.run()
