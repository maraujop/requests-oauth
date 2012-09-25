version:
	git describe --tags > version.txt
	perl -p -i -e 's/-/_/g' version.txt

sdist:
	python setup.py sdist

signed-rpm: sdist version
	rpmbuild -ba python-requests-oauth.spec --sign --define "_sourcedir `pwd`/dist"

rpm: sdist version
	rpmbuild -ba python-requests-oauth.spec --define "_sourcedir `pwd`/dist"

srpm: sdist version
	rpmbuild -bs python-requests-oauth.spec --define "_sourcedir `pwd`/dist"

pylint:
	pylint --rcfile=pylint.conf oauth_hook

unittests:
	python -m unittest discover -v

clean:
	rm -rf MANIFEST build dist python-requests-oauth.spec version.txt
