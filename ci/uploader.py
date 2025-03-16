"""
uploads website to ftp server
"""

import os
import ftplib
import ssl


def render_path(pathlist):
    return '/' + '/'.join(pathlist)


class DirTree(object):
    def __init__(self, ls_func, path=None):
        if path is None:
            self._path = []
        else:
            self._path = path
        self._files = None
        self._folders = None
        self._ls_func = ls_func

    def load(self):
        files, folders = self._ls_func(self._path)
        self._files = set(files)
        self._folders = {folder:DirTree(self._ls_func, self._path + [folder])
                         for folder in folders}

    def cached_deepload(self):
        if not self.is_resolved:
            self.load()
        for dirtree in self._folders.values():
            dirtree.cached_deepload()

    def deepload(self):
        self.load()
        for dirtree in self._folders.values():
            dirtree.deepload()

    @property
    def is_resolved(self):
        return self._files is not None and self._folders is not None

    def lookup(self, path):
        if not self.is_resolved:
            self.load()
        if len(path) == 0:
            return self
        name = path[0]
        if len(path) == 1 and name in self._files:
            return None
        return self._folders[name].lookup(path[1:])

    def invalidate(self, path):
        if not self.is_resolved:
            return
        if len(path) == 0:
            print "INVALIDATED", '/'.join(path)
            self._files = None
            self._folders = None
        else:
            try:
                self._folders[path[0]].invalidate(path[1:])
            except KeyError:
                pass

    def walk(self):
        if not self.is_resolved:
            self.load()
        yield self._path, list(self._folders.keys()), list(self._files)
        for dirtree in self._folders.values():
            for entry in dirtree.walk():
                yield entry

    @property
    def total_element_count(self):
        if not self.is_resolved:
            self.load()
        return len(self._files) + sum(dirtree.total_element_count
                                      for dirtree in self._folders.values())

    def __sub__(self, other):
        def no_ls(path):
            raise RuntimeError('ls not possible on DirTree difference')
        self.cached_deepload()
        if not other.is_resolved:
            other.load()
        new = DirTree(no_ls, self._path)
        new._files = self._files - other._files
        new._folders = {}
        for name, content in self._folders.items():
            if name not in other._folders:
                new._folders[name] = content.stable_copy()
            else:
                sub = content - other._folders[name]
                if sub.total_element_count > 0:
                    new._folders[name] = sub
        return new

    def stable_copy(self):
        def no_ls(path):
            raise RuntimeError('ls not possible on DirTree stable_copy')
        if not self.is_resolved:
            self.load()
        new = DirTree(no_ls, self._path)
        new._files = set(self._files)
        new._folders = {name:content.stable_copy()
                        for name, content
                        in self._folders.items()}
        return new



    def show(self, indent=0):
        spacer = "  "*indent
        if not self.is_resolved:
            yield spacer+"UNRESOLVED"
            return
        for folder, content in sorted(self._folders.items()):
            yield spacer+"\\" + folder
            for line in content.show(indent+1):
                yield line
        for file in sorted(self._files):
            yield spacer+file

    def __str__(self):
        return "\n".join(self.show())

def local_dirtree(folder):
    folder = os.path.abspath(folder)
    def ls_func(path):
        path = os.path.join(folder, *path)
        files = []
        folders = []
        for el in os.listdir(path):
            if os.path.isdir(os.path.join(path, el)):
                folders.append(el)
            else:
                files.append(el)
        return files, folders
    return DirTree(ls_func)


class FTPClient(object):
    """
    More advanced FTP client than ftplib
    """
    def __init__(self, host, user, password):
        self._ftp = ftplib.FTP_TLS(host, user, password)
        self._dirtree = DirTree(self._ls)

    def _ls(self, path=None):
        if path is None:
            path = []
        print "LS", path
        lines = []
        self._ftp.retrlines('LIST %s'%render_path(path), lines.append)
        files = []
        folders = []
        for line in lines:
            (permission,
             count,
             user,
             group,
             size,
             month,
             day,
             year,
             filename) = line.split(None,8)
            if permission[0] == 'd':
                folders.append(filename)
            else:
                files.append(filename)
        return files, folders

    def get(self, path):
        return self._dirtree.lookup(path)

    def deepls(self):
        self._dirtree.deepload()

    def ls(self, path):
        return self._dirtree.lookup(path)

    def mkdir(self, path):
        try:
            res = self._dirtree.lookup(path)
        except KeyError:
            self.mkdir(path[:-1])
            print "MKDIR", render_path(path)
            self._ftp.mkd('/'.join(path))
            self._dirtree.invalidate(path[:-1])
            return
        if not isinstance(res, DirTree):
            raise ValueError('exists as file')

    def delete(self, path):
        print "DELETE", render_path(path)
        self._ftp.delete('/'.join(path))

    def send_tree(self, path, source_path, tree_to_send, delete_other=False):
        delete_tree = self._dirtree.lookup(path)-tree_to_send
        print delete_tree
        for root, folders, files in tree_to_send.walk():
            for filename in files:
                source = [source_path] + root + [filename]
                target_dir = path + root
                target = target_dir + [filename]
                try:
                    self._dirtree.lookup(target_dir)
                except KeyError:
                    self.mkdir(target_dir)
                print "SEND", '/'.join(source), "->",
                print '/'.join(path + root)
                with open(os.sep.join(source)) as file_to_send:
                    self._ftp.storbinary("STOR %s"%render_path(target),
                                         file_to_send)
        if delete_other:
            for root, folders, files in delete_tree.walk():
                for filename in files:
                    self.delete(root + [filename])


def _main():
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    import yaml
    logindata = yaml.load(open(os.path.join(BASEDIR, 'login.yaml')))
    ftpclient = FTPClient(**logindata)
    #print ftpclient.ls(['wwwroot'])
    #ftpclient.deepls()
    wwwroot = ftpclient.get(['wwwroot'])
    print wwwroot
    localdir = local_dirtree('../htdocs')
    ftpclient.send_tree(['wwwroot'], '../htdocs', localdir, True)

if __name__ == '__main__':
    _main()
