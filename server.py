# -*- coding: utf-8 -*-
import os
import tornado.ioloop
import tornado.web
import scss

scss.config.PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "templates", "scss")

nav = [('Gitarren', '/gitarren.html'),
       ('Werkstatt', '/werkstatt.html'),
       ('Über Mich', '/uebermich.html'),
       ('Kontakt', '/kontakt.html')]

class MainHandler(tornado.web.RequestHandler):
    def get(self, page="base.html"):
        if page == "home.html":
            page = "base.html"
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.set_header('Cache-Control', 'must-revalidate; max-age=0')
        self.render(page,
                css_dir="",
                navitems=nav)

class StartHandler(tornado.web.RequestHandler):
    def get(self, page="start.html"):
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.set_header('Cache-Control', 'must-revalidate; max-age=0')
        self.render(page,
                css_dir="",
                navitems=nav)

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
                (r"/(.+\.html)", MainHandler),
                (r"/stylesheet.css", StylesheetHandler),
            ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            )
        super(Application, self).__init__(handlers, **settings)

if __name__ == "__main__":
    application = Application()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

