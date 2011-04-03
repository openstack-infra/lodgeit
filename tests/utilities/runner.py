from werkzeug import create_environ
from lodgeit.application import make_app


foo = make_app('sqlite://', 'NONE', False, True)
