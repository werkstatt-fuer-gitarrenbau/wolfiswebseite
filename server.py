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
                ('Gebrauchtes', 'gebrauchtes.html'),
                ('Reparaturen', 'reparaturen.html'),
                ('Restauration', 'restauration.html'),]

def load_guitar_info(folder):
    with open(os.path.join(folder, 'gitarren.yaml'),
              'r') as guitar_list_file:
        guitar_list = yaml.load(guitar_list_file)
    def load_single_guitar_info(guitar):
        guitars_folder = os.path.join(folder, 'gitarren')
        guitar_folder = os.path.join(guitars_folder, guitar)
        try:
            with open(os.path.join(guitar_folder,
                                   '%s.yaml' % guitar)) as guitar_info:
                res = yaml.load(guitar_info)
        except IOError:
            res = {'name': guitar}
        res['folder'] = guitar
        prefix_len = len(guitars_folder + os.path.sep)
        images = sorted(glob.glob(os.path.join(guitar_folder, '*.jpg')))
        res['images'] = [path[prefix_len:] for path in images]
        res['images_small'] = [name.replace('.jpg', '.300.jpg')
                               for name in res['images']]
        return res
    return map(load_single_guitar_info, guitar_list)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.guitar_info = \
            load_guitar_info(os.path.join(self.settings["data_path"],
                                          'gitarren_neubau'))

    def render(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.set_header('Cache-Control', 'must-revalidate; max-age=0')
        kwargs['css_dir'] = ""
        kwargs['navitems'] = NAV
        kwargs['gitarren_nav'] = GITARREN_NAV
        kwargs['guitar_info'] = self.guitar_info
        super(BaseHandler, self).render(*args, **kwargs)

class MainHandler(BaseHandler):
    def get(self, page="base.html"):
        if page == "home.html":
            page = "base.html"
        self.render(page)

class GitarrenNeubauHandler(BaseHandler):
    def get(self, guitar):
        guitar_by_folder = {g['folder']:g for g in self.guitar_info}
        guitar = guitar_by_folder[guitar]
        self.render("gitarren_neubau.html",
                guitar=guitar)

class GitarrenNeubauImageHandler(tornado.web.RequestHandler):
    def get(self, image, size=None):
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
                               'gitarren_neubau',
                               'gitarren',
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
                (r"/gitarren/neubau/(.+)\.html", GitarrenNeubauHandler),
                (r"/gitarren/neubau/(?P<image>[^\.]+)(?:\.(?P<size>[0-9]+))?\.jpg", GitarrenNeubauImageHandler),
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

