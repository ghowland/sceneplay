rm -rf dist/ build/

#py2applet --make-setup owr.py --site-packages --iconfile speedometer.icns --resources resources/ 

if [ "$1" == "" ] ; then
  python2.6 setup.py py2app -A
else
  python2.6 setup.py py2app
fi

mv dist/owr.app dist/tower.app
open dist/tower.app

