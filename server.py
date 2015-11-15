# -*- coding: utf-8 -*-
import os
import sys
import tornado.ioloop
import tornado.web
import scss
import yaml
import glob
import StringIO
from PIL import Image
import markdown2

scss.config.PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "templates", "scss")

NAV = [('Gitarren', '/gitarren.html'),
       ('Werkstatt', '/werkstatt.html'),
       ('Über Mich', '/uebermich.html'),
       ('Kontakt', '/kontakt.html')]
GITARREN_NAV = [('Neubau', 'neubau.html', 'neubau'),
                ('Gebrauchtes', 'gebraucht.html', 'gebraucht'),
                ('Reparaturen', 'reparaturen.html', 'reparatur')]

GITARREN_EIGENSCHAFTEN = [('wood', 'Holz'),
                          ('wood_and_other', 'Hölzer & Ausstattung'),
                          ('other', ''),
                          ('system', 'System'),
                          ('lacquer', 'Lack'),
                          ('condition', 'Zustand'),
                          ('price', 'Preis')]

def aspect((x, y)):
    return 'portrait' if x < y else 'landscape'

def format_text(text):
    return markdown2.markdown(text)

def load_guitar_info(folder):
    with open(os.path.join(folder, 'gitarren.yaml'),
              'r') as guitars_file:
        guitars = yaml.load(guitars_file)
    def load_single_guitar_info(kind, guitar):
        guitars_folder = os.path.join(folder, kind)
        guitar_folder = os.path.join(guitars_folder, guitar)
        try:
            with open(os.path.join(guitar_folder,
                                   '%s.yaml' % guitar)) as guitar_info:
                res = yaml.load(guitar_info)
                if not 'text' in res:
                    res['text'] = ""
        except IOError:
            res = {'name': guitar,
                   'properties': {},
                   'text': ""}
        res['folder'] = guitar
        prefix_len = len(guitars_folder + os.path.sep)
        images = sorted(glob.glob(os.path.join(guitar_folder, '*.jpg')))
        image_sizes = []
        for image in images:
            with open(image) as fil:
                image_sizes.append(Image.open(fil).size)
        res['images'] = [(path[prefix_len:-4], size)
                         for path, size
                         in zip(images, image_sizes)]
        moodimages = [path for path, _ in res['images'] if 'front' in path]
        if len(moodimages) > 0:
            res['moodimage'] = moodimages[0]
            res['images'] = [info
                             for info in res['images']
                             if info[0] != moodimages[0]]
        else:
            res['moodimage'] = res['images'][0][0]
        res['images'] = [(path, size, aspect(size) != aspect(size2))
                         for (path, size), (_, size2)
                         in zip(res['images'],
                                res['images'][1:] + res['images'][-1:])]
        return res
    return {kind: [load_single_guitar_info(kind, guitar) for guitar in guitar_list]
            for kind, guitar_list in guitars.items()}

def load_image_names(folder):
    images = sorted(glob.glob(os.path.join(folder, '*.jpg')))
    print images
    return [os.path.split(image)[1][:-4] for image in images]

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.guitar_info = \
            load_guitar_info(os.path.join(self.settings["data_path"],
                                          'gitarren'))
        self.werkstatt_bilder = \
            load_image_names(os.path.join('assets', 'werkstatt'))

    def render(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.set_header('Cache-Control', 'must-revalidate; max-age=0')
        kwargs['css_dir'] = ""
        kwargs['navitems'] = NAV
        kwargs['gitarren_nav'] = GITARREN_NAV
        if not 'gitarren_nav_img' in kwargs:
            kwargs['gitarren_nav_img'] = False
        kwargs['format_text'] = format_text
        kwargs['werkstatt_bilder'] = self.werkstatt_bilder
        super(BaseHandler, self).render(*args, **kwargs)

class MainHandler(BaseHandler):
    def get(self, page="base.html"):
        if page == "home.html":
            page = "base.html"
        self.render(page, gitarren_nav_img=True)

class GitarrenIndexHandler(BaseHandler):
    def get(self, kind):
        self.render("gitarren/%s.html" % kind,
                    guitar_kind=kind,
                    guitar_info=self.guitar_info.get(kind, []))


class GitarrenHandler(BaseHandler):
    def get(self, kind, guitar):
        guitar_by_folder = {g['folder']:g for g in self.guitar_info[kind]}
        guitar = guitar_by_folder[guitar]
        self.render("gitarren_detail.html",
                    guitar=guitar,
                    guitar_properties=GITARREN_EIGENSCHAFTEN)


class ImageHandler(tornado.web.RequestHandler):
    def deliver(self, filename, size):
        if size is None:
            def resize(fil):
                return fil
        else:
            size = int(size)
            def resize(fil):
                sio = StringIO.StringIO()
                img = Image.open(fil)
                img.thumbnail((size, size), Image.ANTIALIAS)
                img.save(sio, "JPEG")
                sio.seek(0)
                return sio
        self.set_header('Content-Type', 'image/jpeg')
        with open(filename) as img_file:
            self.write(resize(img_file).read())


class GitarrenImageHandler(ImageHandler):
    def get(self, kind, image, size=None):
        self.deliver(os.path.join(self.settings['data_path'],
                                  'gitarren',
                                  kind,
                                  '%s.jpg' % image),
                     size)

class AssetImageHandler(ImageHandler):
    def get(self, path, size=None):
        self.deliver(os.path.join('assets', path) + '.jpg', size)

class StartHandler(tornado.web.RequestHandler):
    def get(self, page="start.html"):
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.set_header('Cache-Control', 'must-revalidate; max-age=0')
        self.render(page,
                css_dir="",
                navitems=NAV)

class StylesheetHandler(tornado.web.RequestHandler):
    compiler = scss.Scss(scss_opts={
        'compress': True,
        'debug_info': False,
    })
    def get(self):
        self.set_header('Content-Type', 'text/css; charset=utf-8')
        self.write(open(os.path.join(scss.config.PROJECT_ROOT, 'reset.css')).read())
        self.write(self.compiler.compile(scss_file=os.path.join(scss.config.PROJECT_ROOT, 'stylesheet.scss')))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", StartHandler),
                (r"/gitarren/(?P<kind>[a-z]+).html", GitarrenIndexHandler),
                (r"/gitarren/(?P<kind>[a-z]+)/(?P<guitar>.+)\.html", GitarrenHandler),
                (r"/gitarren/(?P<kind>[a-z]+)/(?P<image>[^\.]+)(?:\.(?P<size>[0-9]+))?\.jpg", GitarrenImageHandler),
                (r"/images/(?P<path>[^\.]+)(?:\.(?P<size>[0-9]+))?\.jpg", AssetImageHandler),
                (r"/([^/\\]+\.html)", MainHandler),
                (r"/(gitarren/[^/\\]+\.html)", MainHandler),
                (r"/stylesheet.css", StylesheetHandler),
            ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            data_path=os.path.join(os.path.dirname(__file__), "data"),
            debug=True,
            )
        super(Application, self).__init__(handlers, **settings)

if __name__ == "__main__":
    application = Application()
    application.listen(8888)
    print "started server on http://localhost:8888"
    tornado.ioloop.IOLoop.instance().start()
