from lodgeit.application import make_app
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_simple

app = DebuggedApplication(make_app('sqlite:////tmp/lodgeit.db'))
run_simple('localhost', 7000, app, True)
