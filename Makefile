.PHONY: help clean server shell reset extract-messages

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  clean                 delete all compiled python and backup files"
	@echo "  server                start the development server"
	@echo "  shell                 start a development shell"
	@echo "  extract-messages      update the pot file"
	@echo "  update-translations   update the translations"
	@echo "  compile-translations  compile all translation files"

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

server:
	@(python manage.py runserver)

shell:
	@(python manage.py shell)

extract-messages:
	pybabel extract -F babel.ini -o lodgeit/i18n/messages.pot .

update-translations:
	pybabel update -ilodgeit/i18n/messages.pot -dlodgeit/i18n -Dmessages

compile-translations:
	pybabel compile -dlodgeit/i18n --statistics
