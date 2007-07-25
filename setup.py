#! /usr/bin/env python

import sys, os, glob
from distutils.core import setup
from distutils.sysconfig import PREFIX
from getopt import getopt

prefix = None
if len (sys.argv) > 2:
    opts, args = getopt (sys.argv[2:], "", ['prefix='])
    for o, a in opts:
        if o == "--prefix":
            prefix = a
            break
if not prefix and "PREFIX" in os.environ:
    prefix = os.environ["PREFIX"]
    sys.argv += ["--prefix", prefix]
else:
    prefix = PREFIX

f = open (os.path.join ("ccm/Constants.py.in"), "rt")
data = f.read ()
f.close ()
data = data.replace ("@prefix@", prefix)
f = open (os.path.join ("ccm/Constants.py"), "wt")
f.write (data)
f.close ()

def filter_images (image):
    return image.startswith ("plugin-") or image.startswith ("category-")

images = map (lambda i: "images/%s" % i, 
              filter (filter_images, os.listdir ("images")))

data_files = [
                ("share/icons/hicolor/scalable/apps", ["images/ccsm.svg"]),
                ("share/pixmaps", ["images/ccsm.png"]),
                ("share/applications", ["ccsm.desktop"]),
                ("share/ccsm/images", images)
             ]

if len (sys.argv) == 1 or sys.argv[1] not in ("install", "build"):
    print "Please specify operation : install | build"
    raise SystemExit

podir = os.path.join (os.path.realpath ("."), "po")
if os.path.isdir (podir):
    buildcmd = "msgfmt -o build/locale/%s/ccsm.mo po/%s.po"
    mopath = "build/locale/%s/ccsm.mo"
    destpath = "share/locale/%s/LC_MESSAGES"
    for name in os.listdir (podir):
        if name[-2:] == "po":
            name = name[:-3]
            if not os.path.isdir ("build/locale/" + name):
                os.makedirs ("build/locale/" + name)
            os.system (buildcmd % (name, name))
            data_files.append ((destpath % name, [mopath % name]))

setup (
        name             = "ccsm",
        version          = "0.0.0",
        description      = "OpenGL Fragment and Vertex Program editor",
        author           = "Patrick Niklaus",
        author_email     = "marex@opencompositing.org",
        url              = "http://opencompositing.org/",
        license          = "GPL",
        data_files       = data_files,
        packages         = ["ccm"],
        scripts          = ["ccsm"]
     )

os.remove ("ccm/Constants.py")
