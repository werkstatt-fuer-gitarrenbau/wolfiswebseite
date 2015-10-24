# -*- coding: utf-8 -*-
import os
import tornado.ioloop
import tornado.web
import scss
import yaml
import glob
import StringIO
from PIL import Image

scss.config.PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "templates", "scss")

NAV = [('Gitarren', '/gitarren.html'),
       ('Werkstatt', '/werkstatt.html'),
       ('Über Mich', '/uebermich.html'),
       ('Kontakt', '/kontakt.html')]

GITARREN_NAV = [('Neubau', 'neubau.html'),
                ('Gebrauchtes', 'gebraucht.html'),
                ('Reparaturen', 'reparaturen.html'),
                ('Restauration', 'restauration.html'),]

GITARREN_EIGENSCHAFTEN = [('wood', 'Holz'),
                          ('other', ''),
                          ('system', 'System'),
                          ('lacquer', 'Lack'),
                          ('condition', 'Zustand'),
                          ('price', 'Preis')]

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
        res['images'] = [path[prefix_len:-4] for path in images]
        moodimages = [path for path in res['images'] if 'front' in path]
        if len(moodimages) > 0:
            res['moodimage'] = moodimages[0]
            res['images'] = [path
                             for path in res['images']
                             if path != moodimages[0]]
        else:
            res['moodimage'] = res['images'][0]
        return res
    return {kind: [load_single_guitar_info(kind, guitar) for guitar in guitar_list]
            for kind, guitar_list in guitars.items()}

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.guitar_info = \
            load_guitar_info(os.path.join(self.settings["data_path"],
                                          'gitarren'))

    def render(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.set_header('Cache-Control', 'must-revalidate; max-age=0')
        kwargs['css_dir'] = ""
        kwargs['navitems'] = NAV
        kwargs['gitarren_nav'] = GITARREN_NAV
        super(BaseHandler, self).render(*args, **kwargs)

class MainHandler(BaseHandler):
    def get(self, page="base.html"):
        if page == "home.html":
            page = "base.html"
        self.render(page)

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

class GitarrenImageHandler(tornado.web.RequestHandler):
    def get(self, kind, image, size=None):
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
        self.set_header('Content-Type', 'image/jpeg; charset=utf-8')
        with open(os.path.join(self.settings['data_path'],
                               'gitarren',
                               kind,
                               '%s.jpg' % image)) as img_file:
            self.write(resize(img_file).read())

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

