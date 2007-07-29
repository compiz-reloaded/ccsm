#!/usr/bin/env python

import sys, os, glob
from distutils.core import setup
from distutils.command.install import install as _install

INSTALLED_FILES = "installed_files"

class install (_install):

    def run (self):
        _install.run (self)
        outputs = self.get_outputs()
        length = 0
        if self.root:
            length += len (self.root)
        if self.prefix:
            length += len (self.prefix)
        if length:
            for counter in xrange (len (outputs)):
                outputs[counter] = outputs[counter][length:]
        data = "\n".join (outputs)
        try:
            file = open (INSTALLED_FILES, "w")
        except:
            self.warn ("Could not write installed files list %s" % \
                       INSTALLED_FILES)
            return 
        file.write (data)
        file.close ()

class uninstall (_install):

    def run (self):
        try:
            file = open (INSTALLED_FILES, "r")
        except:
            self.warn ("Could not read installed files list %s" % \
                       INSTALLED_FILES)
            return 
        files = file.readlines ()
        file.close ()
        prepend = ""
        if self.root:
            prepend += self.root
        if self.prefix:
            prepend += self.prefix
        if len (prepend):
            for counter in xrange (len (files)):
                files[counter] = prepend + files[counter].rstrip ()
        for file in files:
            print "Uninstalling %s" % file
            try:
                os.unlink (file)
            except:
                self.warn ("Could not remove file %s" % file)

ops = ("install", "build", "sdist", "uninstall", "clean")

if not len (sys.argv) >= 2 or sys.argv[1] not in ops:
    print "Please specify operation : %s" % " | ".join (ops)
    raise SystemExit

prefix = None
if len (sys.argv) > 2:
    i = 0
    for o in sys.argv:
        if o.startswith ("--prefix"):
            if o == "--prefix":
                if len (sys.argv) >= i:
                    prefix = sys.argv[i + 1]
                sys.argv.remove (prefix)
            elif o.startswith ("--prefix=") and len (o[9:]):
                prefix = o[9:]
            sys.argv.remove (o)
            break
        i += 1
if not prefix and "PREFIX" in os.environ:
    prefix = os.environ["PREFIX"]
if not prefix or not len (prefix):
    prefix = "/usr/local"

if sys.argv[1] in ("install", "uninstall") and len (prefix):
    sys.argv += ["--prefix", prefix]

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

version_file = open ("VERSION", "r")
version = version_file.read ().strip ()
if "=" in version:
    version = version.split ("=")[1]

setup (
        name             = "ccsm",
        version          = version,
        description      = "CompizConfig Settings Manager",
        author           = "Patrick Niklaus",
        author_email     = "marex@opencompositing.org",
        url              = "http://opencompositing.org/",
        license          = "GPL",
        data_files       = data_files,
        packages         = ["ccm"],
        scripts          = ["ccsm"],
        cmdclass         = {"uninstall" : uninstall,
                            "install" : install}
     )

os.remove ("ccm/Constants.py")
